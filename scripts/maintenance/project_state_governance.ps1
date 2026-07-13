<#
.SYNOPSIS
    FleetVision 方案 C：Repository-backed project state migration and governance audit.

.DESCRIPTION
    Windows PowerShell 5.1 compatible.
    Four explicit modes:
      Audit      - Read-only worktree/content inventory; git fetch updates remote refs only.
      Apply      - Creates/updates governance Markdown through managed blocks. No commit or push.
      Verify     - Verifies only authorized governance paths changed.
      CommitPush - Stages only authorized governance files, commits, pushes main, and verifies remote HEAD.

    Safety model:
      - Requires branch main.
      - Requires local HEAD == origin/main == GitHub ls-remote main before Apply/CommitPush.
      - Allows only a clean worktree or the protected untracked directory:
            outputs/metadata/external_assets/
      - Never stages, deletes, or modifies the protected untracked directory.
      - Refuses to proceed if canonical/raw/registry paths show tracked changes.
      - Backs up every touched existing file outside the repository before Apply.

.NOTES
    Project root default: G:\Project\FleetVision
    Initial expected HEAD: 16e08121da22bf59989f1b2de5882274d30a2b4a
#>

[CmdletBinding()]
param(
    [ValidateSet("Audit", "Apply", "Verify", "CommitPush")]
    [string]$Mode = "Audit",

    [string]$ProjectRoot = "G:\Project\FleetVision",

    [string]$ExpectedHead = "16e08121da22bf59989f1b2de5882274d30a2b4a",

    [switch]$IncludeLargeDirectoryInventory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptVersion = "1.0.5"
$ScriptSourcePath = $PSCommandPath
$ProtectedUntrackedPath = "outputs/metadata/external_assets"
$TechnicalPhase = "04.5K"
$GovernanceGate = "GOV-C-01"
$GovernanceClassification = "PROJECT_GOVERNANCE_SOURCE_OF_TRUTH_ESTABLISHED"

$ManagedRelativePaths = @(
    "AGENTS.md",
    "PROJECT_CONTEXT_BRIEF.md",
    "docs/00_project_management/START_HERE.md",
    "docs/00_project_management/PROJECT_STATUS.md",
    "docs/00_project_management/MASTER_PHASE_MAP.md",
    "docs/00_project_management/WORKFLOW_GOVERNANCE.md",
    "docs/00_project_management/PROTECTED_ASSETS.md",
    "docs/00_project_management/DECISION_LOG.md",
    "docs/00_project_management/HANDOFF_CURRENT.md",
    "docs/00_project_management/NEW_CHAT_BOOTSTRAP.md",
    "docs/00_project_management/PROJECT_INVENTORY.md",
    "docs/00_project_management/phase_logs/PHASE_04_5_LOG.md",
    "scripts/maintenance/project_state_governance.ps1"
)

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ("===== {0} =====" -f $Title)
}

function Normalize-RepoRelativePath {
    param([string]$PathValue)
    if ($null -eq $PathValue) { return "" }
    return (($PathValue.Trim() -replace "\\", "/").TrimEnd("/"))
}

function Invoke-Git {
    param(
        [Parameter(Mandatory=$true)]
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    $output = @()
    $exitCode = $null
    $previousErrorActionPreference = $ErrorActionPreference

    try {
        # Windows PowerShell 5.1 can promote native stderr text to a terminating
        # NativeCommandError when the script-level preference is Stop.
        # Treat Git as failed only when its process exit code is non-zero.
        $ErrorActionPreference = "Continue"
        $output = & git -C $ProjectRoot @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    $text = (($output | ForEach-Object { [string]$_ }) -join "`n").TrimEnd()

    if ((-not $AllowFailure) -and $exitCode -ne 0) {
        throw ("git {0} failed with exit code {1}:`n{2}" -f ($Arguments -join " "), $exitCode, $text)
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Text = $text
    }
}

function Assert-ProjectRoot {
    if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
        throw "Project root does not exist: $ProjectRoot"
    }

    $resolved = (Resolve-Path -LiteralPath $ProjectRoot).Path
    $gitRootResult = Invoke-Git -Arguments @("rev-parse", "--show-toplevel")
    $gitRoot = $gitRootResult.Text.Trim()

    if ([string]::IsNullOrWhiteSpace($gitRoot)) {
        throw "Not a Git repository: $ProjectRoot"
    }

    $resolvedNormalized = ($resolved.TrimEnd("\") -replace "\\", "/").ToLowerInvariant()
    $gitNormalized = ($gitRoot.TrimEnd("/") -replace "\\", "/").ToLowerInvariant()

    if ($resolvedNormalized -ne $gitNormalized) {
        throw "ProjectRoot is not the repository root. Expected $gitRoot but received $resolved"
    }
}

function Get-StatusAssessment {
    $statusResult = Invoke-Git -Arguments @("status", "--porcelain=v1", "--untracked-files=normal")
    $lines = @()

    if (-not [string]::IsNullOrWhiteSpace($statusResult.Text)) {
        $lines = @($statusResult.Text -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    }

    $unexpected = New-Object System.Collections.Generic.List[string]
    $protectedSeen = $false

    foreach ($line in $lines) {
        if ($line.Length -lt 4) {
            $unexpected.Add($line)
            continue
        }

        $code = $line.Substring(0, 2)
        $pathPart = $line.Substring(3)
        if ($pathPart -match " -> ") {
            $pathPart = ($pathPart -split " -> ")[-1]
        }
        $normalized = Normalize-RepoRelativePath $pathPart

        if ($code -eq "??" -and $normalized -eq $ProtectedUntrackedPath) {
            $protectedSeen = $true
        }
        else {
            $unexpected.Add($line)
        }
    }

    $classification = "CLEAN"
    if ($unexpected.Count -gt 0) {
        $classification = "UNEXPECTED_CHANGES"
    }
    elseif ($protectedSeen) {
        $classification = "PROTECTED_UNTRACKED_ONLY"
    }

    return [pscustomobject]@{
        Lines = $lines
        UnexpectedLines = $unexpected.ToArray()
        ProtectedUntrackedSeen = $protectedSeen
        Classification = $classification
    }
}

function Get-RemoteHeadFromLsRemote {
    $result = Invoke-Git -Arguments @("ls-remote", "origin", "refs/heads/main") -AllowFailure
    if ($result.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($result.Text)) {
        return [pscustomobject]@{
            Success = $false
            Head = ""
            Error = $result.Text
        }
    }

    $firstLine = ($result.Text -split "`r?`n")[0]
    $head = ($firstLine -split "\s+")[0].Trim()
    return [pscustomobject]@{
        Success = $true
        Head = $head
        Error = ""
    }
}

function Get-RepoState {
    param([switch]$FetchRemote)

    if ($FetchRemote) {
        $fetch = Invoke-Git -Arguments @("fetch", "origin", "--prune") -AllowFailure
        $fetchSuccess = ($fetch.ExitCode -eq 0)
        $fetchMessage = $fetch.Text
    }
    else {
        $fetchSuccess = $true
        $fetchMessage = "NOT_REQUESTED"
    }

    $branch = (Invoke-Git -Arguments @("rev-parse", "--abbrev-ref", "HEAD")).Text.Trim()
    $localHead = (Invoke-Git -Arguments @("rev-parse", "HEAD")).Text.Trim()
    $originMainResult = Invoke-Git -Arguments @("rev-parse", "origin/main") -AllowFailure
    $originMain = ""
    if ($originMainResult.ExitCode -eq 0) {
        $originMain = $originMainResult.Text.Trim()
    }

    $remote = Get-RemoteHeadFromLsRemote
    $status = Get-StatusAssessment
    $remoteUrl = (Invoke-Git -Arguments @("remote", "get-url", "origin")).Text.Trim()
    $subject = (Invoke-Git -Arguments @("log", "-1", "--pretty=%s")).Text.Trim()
    $trackedCountText = (Invoke-Git -Arguments @("ls-files")).Text
    $trackedCount = 0
    if (-not [string]::IsNullOrWhiteSpace($trackedCountText)) {
        $trackedCount = @($trackedCountText -split "`r?`n").Count
    }

    $trackedMdText = (Invoke-Git -Arguments @("ls-files", "*.md")).Text
    $trackedMd = @()
    if (-not [string]::IsNullOrWhiteSpace($trackedMdText)) {
        $trackedMd = @($trackedMdText -split "`r?`n" | Where-Object { $_ -ne "" } | Sort-Object)
    }

    $localVsOrigin = ""
    if (-not [string]::IsNullOrWhiteSpace($originMain)) {
        $localVsOrigin = (Invoke-Git -Arguments @("rev-list", "--left-right", "--count", "origin/main...HEAD")).Text.Trim()
    }

    return [pscustomobject]@{
        ScriptVersion = $ScriptVersion
        Timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
        ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
        Branch = $branch
        LocalHead = $localHead
        OriginMain = $originMain
        GitHubRemoteHead = $remote.Head
        GitHubRemoteReachable = $remote.Success
        GitHubRemoteError = $remote.Error
        FetchSuccess = $fetchSuccess
        FetchMessage = $fetchMessage
        RemoteUrl = $remoteUrl
        CommitSubject = $subject
        LocalVsOrigin = $localVsOrigin
        StatusClassification = $status.Classification
        StatusLines = @($status.Lines)
        UnexpectedStatusLines = @($status.UnexpectedLines)
        ProtectedUntrackedSeen = $status.ProtectedUntrackedSeen
        TrackedFileCount = $trackedCount
        TrackedMarkdownFiles = $trackedMd
    }
}

function Assert-SafeSynchronizedState {
    param(
        [Parameter(Mandatory=$true)]
        $State,
        [switch]$RequireExpectedHead,
        [switch]$AllowManagedChanges
    )

    if (-not $State.FetchSuccess) {
        throw "git fetch origin failed. Refusing to continue."
    }
    if (-not $State.GitHubRemoteReachable) {
        throw "GitHub remote main could not be resolved with git ls-remote. Refusing to continue."
    }
    if ($State.Branch -ne "main") {
        throw "Current branch must be main. Actual: $($State.Branch)"
    }
    if ([string]::IsNullOrWhiteSpace($State.OriginMain)) {
        throw "origin/main is unavailable."
    }
    if ($State.LocalHead -ne $State.OriginMain) {
        throw "Local HEAD and origin/main differ. Local=$($State.LocalHead), origin/main=$($State.OriginMain)"
    }
    if ($State.LocalHead -ne $State.GitHubRemoteHead) {
        throw "Local HEAD and GitHub remote main differ. Local=$($State.LocalHead), remote=$($State.GitHubRemoteHead)"
    }
    if ($RequireExpectedHead -and $State.LocalHead -ne $ExpectedHead) {
        throw "HEAD does not match ExpectedHead. Expected=$ExpectedHead, actual=$($State.LocalHead)"
    }

    if ($State.StatusClassification -eq "UNEXPECTED_CHANGES") {
        if (-not $AllowManagedChanges) {
            throw ("Unexpected worktree changes detected:`n{0}" -f ($State.UnexpectedStatusLines -join "`n"))
        }

        $managedChanges = Assert-OnlyManagedChanges
        if ($managedChanges.Count -eq 0) {
            throw "AllowManagedChanges was requested, but no allowlisted governance changes were found."
        }
    }
}

function Get-FileSha256OrMissing {
    param([string]$FullPath)
    if (-not (Test-Path -LiteralPath $FullPath -PathType Leaf)) {
        return "MISSING"
    }
    return (Get-FileHash -LiteralPath $FullPath -Algorithm SHA256).Hash
}

function Get-DirectoryInventory {
    param([switch]$Deep)

    $rows = New-Object System.Collections.Generic.List[object]
    $rootInfo = Get-Item -LiteralPath $ProjectRoot

    $directories = @(Get-ChildItem -LiteralPath $ProjectRoot -Directory -Force |
        Where-Object { $_.Name -ne ".git" } |
        Sort-Object Name)

    foreach ($directory in $directories) {
        $fileCount = $null
        $totalBytes = $null
        $inventoryStatus = "SUMMARY_ONLY"

        $shouldCount = $Deep -or ($directory.Name -in @("docs", "scripts", "src", "tests", "configs", "notebooks"))
        if ($shouldCount) {
            $count = [int64]0
            $bytes = [int64]0
            try {
                foreach ($filePath in [System.IO.Directory]::EnumerateFiles(
                    $directory.FullName,
                    "*",
                    [System.IO.SearchOption]::AllDirectories
                )) {
                    $count++
                    try {
                        $bytes += ([System.IO.FileInfo]$filePath).Length
                    }
                    catch {
                        # Continue inventory even if one file is transient or inaccessible.
                    }
                }
                $fileCount = $count
                $totalBytes = $bytes
                $inventoryStatus = "COUNTED"
            }
            catch {
                $fileCount = -1
                $totalBytes = -1
                $inventoryStatus = "COUNT_FAILED: $($_.Exception.Message)"
            }
        }

        $rows.Add([pscustomobject]@{
            Directory = $directory.Name
            FullPath = $directory.FullName
            FileCount = $fileCount
            TotalBytes = $totalBytes
            InventoryStatus = $inventoryStatus
            LastWriteTime = $directory.LastWriteTime.ToString("yyyy-MM-ddTHH:mm:ss")
        })
    }

    return $rows.ToArray()
}

function Get-MarkdownInventory {
    param($State)

    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($relative in $State.TrackedMarkdownFiles) {
        $full = Join-Path $ProjectRoot ($relative -replace "/", "\")
        $length = 0
        $modified = ""
        if (Test-Path -LiteralPath $full -PathType Leaf) {
            $item = Get-Item -LiteralPath $full
            $length = $item.Length
            $modified = $item.LastWriteTime.ToString("yyyy-MM-ddTHH:mm:ss")
        }

        $rows.Add([pscustomobject]@{
            Path = $relative
            Exists = (Test-Path -LiteralPath $full -PathType Leaf)
            SizeBytes = $length
            LastWriteTime = $modified
            SHA256 = Get-FileSha256OrMissing $full
        })
    }
    return $rows.ToArray()
}

function Write-AuditFiles {
    param(
        $State,
        $DirectoryInventory,
        $MarkdownInventory
    )

    $auditRoot = Join-Path $env:TEMP "FleetVision_Governance_Audit"
    New-Item -ItemType Directory -Path $auditRoot -Force | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $jsonPath = Join-Path $auditRoot ("FleetVision_Governance_Audit_{0}.json" -f $stamp)
    $txtPath = Join-Path $auditRoot ("FleetVision_Governance_Audit_{0}.txt" -f $stamp)
    $latestJson = Join-Path $auditRoot "latest_audit.json"
    $latestTxt = Join-Path $auditRoot "latest_audit.txt"

    $payload = [ordered]@{
        repo_state = $State
        directory_inventory = $DirectoryInventory
        markdown_inventory = $MarkdownInventory
        required_governance_paths = $ManagedRelativePaths
    }

    $json = $payload | ConvertTo-Json -Depth 8
    $json | Set-Content -LiteralPath $jsonPath -Encoding UTF8
    $json | Set-Content -LiteralPath $latestJson -Encoding UTF8

    $text = New-Object System.Collections.Generic.List[string]
    $text.Add("===== FLEETVISION GOVERNANCE AUDIT =====")
    $text.Add("Timestamp: $($State.Timestamp)")
    $text.Add("ProjectRoot: $($State.ProjectRoot)")
    $text.Add("Branch: $($State.Branch)")
    $text.Add("LocalHead: $($State.LocalHead)")
    $text.Add("OriginMain: $($State.OriginMain)")
    $text.Add("GitHubRemoteHead: $($State.GitHubRemoteHead)")
    $text.Add("CommitSubject: $($State.CommitSubject)")
    $text.Add("StatusClassification: $($State.StatusClassification)")
    $text.Add("TrackedFileCount: $($State.TrackedFileCount)")
    $text.Add("TrackedMarkdownCount: $($State.TrackedMarkdownFiles.Count)")
    $text.Add("ProtectedUntrackedSeen: $($State.ProtectedUntrackedSeen)")
    $text.Add("UnexpectedStatusLines: $($State.UnexpectedStatusLines.Count)")
    $text.Add("DirectoryInventoryMode: $(if ($IncludeLargeDirectoryInventory) { 'DEEP' } else { 'TARGETED' })")
    $text.Add("AuditJson: $jsonPath")
    $text.Add("AuditText: $txtPath")
    $text.Add("===== END AUDIT =====")
    $text -join "`r`n" | Set-Content -LiteralPath $txtPath -Encoding UTF8
    $text -join "`r`n" | Set-Content -LiteralPath $latestTxt -Encoding UTF8

    return [pscustomobject]@{
        JsonPath = $jsonPath
        TextPath = $txtPath
        LatestJsonPath = $latestJson
        LatestTextPath = $latestTxt
    }
}

function Backup-ManagedFiles {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupRoot = Join-Path $env:TEMP ("FleetVision_Governance_Backup_{0}" -f $stamp)
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null

    foreach ($relative in $ManagedRelativePaths) {
        $source = Join-Path $ProjectRoot ($relative -replace "/", "\")
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            $destination = Join-Path $backupRoot ($relative -replace "/", "\")
            $destinationDir = Split-Path -Parent $destination
            New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
            Copy-Item -LiteralPath $source -Destination $destination -Force
        }
    }

    return $backupRoot
}

function Set-ManagedBlock {
    param(
        [Parameter(Mandatory=$true)][string]$RelativePath,
        [Parameter(Mandatory=$true)][string]$BlockName,
        [Parameter(Mandatory=$true)][string]$Body,
        [string]$DefaultTitle = ""
    )

    $fullPath = Join-Path $ProjectRoot ($RelativePath -replace "/", "\")
    $parent = Split-Path -Parent $fullPath
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    $begin = "<!-- FLEETVISION-MANAGED:$BlockName`:BEGIN -->"
    $end = "<!-- FLEETVISION-MANAGED:$BlockName`:END -->"
    $managed = $begin + "`r`n" + $Body.Trim() + "`r`n" + $end

    $existing = ""
    if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
        $existing = Get-Content -LiteralPath $fullPath -Raw
    }
    elseif (-not [string]::IsNullOrWhiteSpace($DefaultTitle)) {
        $existing = "# $DefaultTitle`r`n"
    }

    $pattern = [regex]::Escape($begin) + ".*?" + [regex]::Escape($end)
    if ([regex]::IsMatch($existing, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
        $newContent = [regex]::Replace(
            $existing,
            $pattern,
            [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $managed },
            [System.Text.RegularExpressions.RegexOptions]::Singleline
        )
    }
    else {
        if (-not [string]::IsNullOrWhiteSpace($existing)) {
            $existing = $existing.TrimEnd() + "`r`n`r`n"
        }
        $newContent = $existing + $managed + "`r`n"
    }

    Set-Content -LiteralPath $fullPath -Value $newContent -Encoding UTF8
}

function Convert-DirectoryInventoryToMarkdown {
    param($Rows)

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("| Directory | File count | Total bytes | Inventory status | Last write |")
    $lines.Add("|---|---:|---:|---|---|")
    foreach ($row in $Rows) {
        $count = ""
        $bytes = ""
        if ($null -ne $row.FileCount) { $count = [string]$row.FileCount }
        if ($null -ne $row.TotalBytes) { $bytes = [string]$row.TotalBytes }
        $statusSafe = ([string]$row.InventoryStatus).Replace("|", "\|")
        $lines.Add("| $($row.Directory) | $count | $bytes | $statusSafe | $($row.LastWriteTime) |")
    }
    return ($lines -join "`r`n")
}

function Convert-MarkdownInventoryToMarkdown {
    param($Rows)

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("| Markdown path | Size | SHA256 |")
    $lines.Add("|---|---:|---|")
    foreach ($row in $Rows) {
        $lines.Add("| ``$($row.Path)`` | $($row.SizeBytes) | ``$($row.SHA256)`` |")
    }
    return ($lines -join "`r`n")
}

function Apply-GovernanceDocuments {
    param(
        $State,
        $DirectoryInventory,
        $MarkdownInventory
    )

    $timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    $directoryTable = Convert-DirectoryInventoryToMarkdown $DirectoryInventory
    $markdownTable = Convert-MarkdownInventoryToMarkdown $MarkdownInventory
    $statusDisplay = if ($State.StatusLines.Count -eq 0) { "(clean)" } else { ($State.StatusLines -join "`r`n") }

    $agentsBody = @"
## FleetVision repository-governance contract

All AI-assisted work must follow this startup order before proposing or executing a change:

1. Read ``docs/00_project_management/START_HERE.md``.
2. Read ``docs/00_project_management/PROJECT_STATUS.md``.
3. Read ``docs/00_project_management/HANDOFF_CURRENT.md``.
4. Read ``docs/00_project_management/PROTECTED_ASSETS.md``.
5. Read the current phase log identified by ``PROJECT_STATUS.md``.
6. Reconcile the documents against the live Git branch, HEAD, ``origin/main``, and worktree status.

### Mandatory operating rules

- Repository root: ``G:\Project\FleetVision``.
- Production branch: ``main``.
- Codex is disabled unless Vincent explicitly reauthorizes it.
- Cursor Agent is disabled unless Vincent explicitly reauthorizes it.
- Do not provide Codex prompts or instruct Cursor Agent to modify, test, commit, or push.
- ChatGPT may provide Windows PowerShell 5.1 scripts and VS Code manual procedures.
- Process one technical Gate at a time.
- High-risk work must use Audit → Apply/Execute → Verify → Commit/Push.
- Never stage, commit, delete, clean, move, or rewrite ``outputs/metadata/external_assets/``.
- Do not directly modify canonical COCO, raw datasets, or Registry assets without a Gate that explicitly authorizes that exact mutation.
- A Gate is not complete until technical verification, project-state documents, Git commit, push, and remote-HEAD verification all agree.
- Live repository facts and cryptographic hashes override narrative summaries when they conflict.
"@
    Set-ManagedBlock -RelativePath "AGENTS.md" -BlockName "GOVERNANCE-CONTRACT" -Body $agentsBody -DefaultTitle "FleetVision Agent Instructions"

    $contextBody = @"
## Repository-backed project state

FleetVision uses the repository as the cross-conversation source of truth. Start every new work session from:

- ``docs/00_project_management/START_HERE.md``
- ``docs/00_project_management/PROJECT_STATUS.md``
- ``docs/00_project_management/HANDOFF_CURRENT.md``

Chat history is supporting context only. It must not override a newer verified repository state.
"@
    Set-ManagedBlock -RelativePath "PROJECT_CONTEXT_BRIEF.md" -BlockName "SOURCE-OF-TRUTH" -Body $contextBody -DefaultTitle "FleetVision Project Context Brief"

    $startHereBody = @"
## Purpose

This file is the mandatory entry point for every new FleetVision conversation or work session.

## Required reading order

1. ``/AGENTS.md``
2. ``/PROJECT_CONTEXT_BRIEF.md``
3. ``docs/00_project_management/WORKFLOW_GOVERNANCE.md``
4. ``docs/00_project_management/PROTECTED_ASSETS.md``
5. ``docs/00_project_management/PROJECT_STATUS.md``
6. ``docs/00_project_management/HANDOFF_CURRENT.md``
7. ``docs/00_project_management/MASTER_PHASE_MAP.md``
8. The current phase log referenced by ``PROJECT_STATUS.md``
9. ``docs/00_project_management/DECISION_LOG.md`` when a prior architectural or governance decision is relevant

## Conflict precedence

When sources disagree, use this order:

1. Live Git facts: branch, local HEAD, ``origin/main``, GitHub remote HEAD, and worktree status
2. SHA256 values calculated from the actual artifact
3. ``PROJECT_STATUS.md``
4. ``HANDOFF_CURRENT.md``
5. Current phase log
6. ``MASTER_PHASE_MAP.md``
7. Historical chat summaries

Do not infer that an operation is repeatable. Any action marked one-time, promotion, canonical mutation, registry mutation, or production mutation requires an explicit precondition Gate.

## Startup acknowledgement

Before any mutation, report:

- repository and branch
- local HEAD, ``origin/main``, and remote HEAD
- current technical Phase
- latest Gate and classification
- worktree classification
- protected assets
- next authorized action
- any detected conflict
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/START_HERE.md" -BlockName "STARTUP-PROTOCOL" -Body $startHereBody -DefaultTitle "FleetVision Start Here"

    $statusBody = @"
## Machine-readable state

````yaml
schema_version: 1
project: FleetVision
repository_root: "G:\Project\FleetVision"
branch: main
local_head_at_governance_migration: "$($State.LocalHead)"
origin_main_at_governance_migration: "$($State.OriginMain)"
github_remote_head_at_governance_migration: "$($State.GitHubRemoteHead)"
technical_phase: "$TechnicalPhase"
latest_repository_checkpoint_subject: "$($State.CommitSubject.Replace('"', '\"'))"
governance_gate: "$GovernanceGate"
governance_gate_outcome: "PASS"
governance_classification: "$GovernanceClassification"
worktree_policy: "CLEAN_OR_PROTECTED_UNTRACKED_ONLY"
protected_untracked_path: "$ProtectedUntrackedPath/"
training_acceptance: "REQUIRES_RECONCILIATION_FROM_AUTHORITATIVE_PHASE_ARTIFACT"
updated_at: "$timestamp"
````

## Current checkpoint

- Technical phase: **$TechnicalPhase**
- Repository checkpoint before governance migration: ``$($State.LocalHead)``
- Commit subject: **$($State.CommitSubject)**
- Governance migration Gate: **$GovernanceGate — PASS when this document is committed and remote-verified**
- Target classification: **$GovernanceClassification**
- Worktree state before Apply: **$($State.StatusClassification)**

## Current authorization

The authorized task is limited to establishing and verifying repository-backed project governance documentation. No canonical dataset, raw dataset, Registry, training artifact, model artifact, or protected external asset may be modified by this Gate.

## Required reconciliation

Detailed training acceptance and the exact technical sub-Gate after the restored Phase 04.5K notebook must be reconciled from the authoritative notebook/output artifacts before the next technical Gate starts.
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/PROJECT_STATUS.md" -BlockName "CURRENT-STATE" -Body $statusBody -DefaultTitle "FleetVision Project Status"

    $phaseMapBody = @"
## Current repository checkpoint

| Area | Status |
|---|---|
| Phase 00–04 | Completed according to prior project governance records; retain existing detailed records |
| Phase 04.5 | In progress |
| Current technical checkpoint | $TechnicalPhase |
| Repository checkpoint | ``$($State.LocalHead)`` |
| Governance migration | $GovernanceGate — PASS after commit/push remote verification |

This managed block is a high-level index. Detailed Gate evidence belongs in phase logs and artifacts, not in this table.
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/MASTER_PHASE_MAP.md" -BlockName "CURRENT-CHECKPOINT" -Body $phaseMapBody -DefaultTitle "FleetVision Master Phase Map"

    $workflowBody = @"
## Repository-backed operating model (Scheme C)

### Source of truth

The Git repository is the formal source of truth for:

- operating rules
- current Phase and Gate
- protected assets
- decisions
- current handoff
- phase-level execution history
- artifact paths, counts, and SHA256 values

Chat summaries are convenience copies and must be reconciled against the repository.

### Gate lifecycle

1. **Audit** — read-only or metadata-only inspection; no worktree mutation.
2. **Apply/Execute** — only the explicitly authorized change.
3. **Verify** — check outputs, invariants, protected assets, and Git diff.
4. **Commit** — stage an exact allowlist only.
5. **Push** — push only after verification.
6. **Remote verification** — require local HEAD = ``origin/main`` = GitHub remote HEAD.
7. **State synchronization** — update ``PROJECT_STATUS.md``, ``HANDOFF_CURRENT.md``, and the current phase log within the same logical Gate.

### Script standards

- Windows PowerShell 5.1 compatible.
- ``Set-StrictMode -Version Latest``.
- ``$ErrorActionPreference = "Stop"``.
- Fail closed when a precondition is unknown.
- Emit one consolidated result block.
- Avoid recursive hashing of large datasets unless a Gate explicitly requires it.
- Record counts, paths, lineage, timestamps, and SHA256 for governed artifacts.

### Git standards

- Production branch: ``main``.
- No force push.
- No broad ``git add .`` or ``git add -A``.
- Stage exact allowlisted paths.
- Never stage the protected external-assets directory.
- Technical changes and documentation state must not contradict each other.
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/WORKFLOW_GOVERNANCE.md" -BlockName "SCHEME-C" -Body $workflowBody -DefaultTitle "FleetVision Workflow Governance"

    $protectedBody = @"
## Protected asset register

| Asset | Protection rule |
|---|---|
| ``outputs/metadata/external_assets/`` | Protected untracked directory. Never stage, commit, delete, clean, move, or rewrite. |
| ``dataset/01_raw/`` and raw external-source roots | Immutable unless a specifically authorized controlled-restore/intake Gate says otherwise. |
| Canonical COCO annotations and canonical dataset manifests | No direct edit. Changes require proposal/staging, audit, promotion authorization, and post-promotion verification. |
| Registry files | No direct edit or repeated promotion. Registry mutation requires an explicit one-time Gate and before/after SHA256. |
| Failed staging and recovery evidence | Preserve until an explicit retention/disposal decision is recorded. |
| Model and training acceptance artifacts | Do not relabel acceptance based on narrative summaries; use authoritative metrics and Gate evidence. |

## Worktree invariant

Permitted final states:

- clean worktree; or
- only ``?? outputs/metadata/external_assets/``

Any other staged, modified, deleted, renamed, or untracked path blocks Apply, Commit, and Push.
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/PROTECTED_ASSETS.md" -BlockName "ASSET-REGISTER" -Body $protectedBody -DefaultTitle "FleetVision Protected Assets"

    $decisionBody = @"
## DEC-GOV-2026-0713-01 — Repository-backed cross-conversation state

**Decision:** Adopt Scheme C: Git repository Markdown is the formal cross-conversation source of truth, combined with a minimal new-chat bootstrap prompt.

**Rationale:** FleetVision has expanding datasets, long-running Phases, many Gates, one-time promotions, protected assets, and cryptographic evidence. Reconstructing state from chat summaries alone creates avoidable omission and staleness risk.

**Consequences:**

- Every new conversation starts from ``START_HERE.md``.
- Gate completion includes project-state document synchronization.
- Large datasets and outputs remain outside Markdown; documents store paths, counts, lineage, timestamps, classifications, and SHA256 values.
- Direct GitHub writes are prohibited when local and remote state have not been reconciled.
- Local HEAD, ``origin/main``, and remote HEAD must agree before controlled repository writes.
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/DECISION_LOG.md" -BlockName "DEC-GOV-2026-0713-01" -Body $decisionBody -DefaultTitle "FleetVision Decision Log"

    $handoffBody = @"
## Repository

- Root: ``G:\Project\FleetVision``
- Branch: ``main``
- Checkpoint before governance migration: ``$($State.LocalHead)``
- Commit: **$($State.CommitSubject)**
- Local/origin/remote agreement at Apply: **verified**

## Current state

- Technical Phase: **$TechnicalPhase**
- Governance Gate: **$GovernanceGate**
- Governance classification: **$GovernanceClassification**
- Worktree policy: clean or protected untracked directory only
- Protected untracked directory: ``outputs/metadata/external_assets/``

## Tool restrictions

- Codex: disabled until explicitly reauthorized
- Cursor Agent: disabled until explicitly reauthorized
- Allowed operating mode: ChatGPT analysis plus Windows PowerShell 5.1 / VS Code controlled execution

## Do not repeat

Do not rerun any prior one-time Registry promotion, canonical promotion, controlled restore, or production mutation unless a new Gate explicitly proves that it is safe and required.

## Next authorized action

Complete governance Apply → Verify → CommitPush. After remote verification, reconcile the exact Phase 04.5K technical sub-Gate and training-acceptance state from authoritative artifacts before starting another technical Gate.
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/HANDOFF_CURRENT.md" -BlockName "CURRENT-HANDOFF" -Body $handoffBody -DefaultTitle "FleetVision Current Handoff"

    $bootstrapBody = @"
## Standard new-conversation prompt

````text
繼續 FleetVision／Project_FleetVision 車損辨識專案。

請先透過 GitHub main branch 讀取：
1. AGENTS.md
2. PROJECT_CONTEXT_BRIEF.md
3. docs/00_project_management/START_HERE.md

再依 START_HERE.md 的指定順序讀取目前專案狀態。

請先核對並回報：
- repository / branch
- local or repository HEAD
- origin/main / remote HEAD（可取得時）
- current technical phase
- latest gate outcome and classification
- worktree classification
- protected assets
- next authorized action
- detected conflicts

未完成狀態核對前，不得提出或執行修改。
Codex 與 Cursor Agent 維持停用，除非 Vincent 明確重新授權。
````
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/NEW_CHAT_BOOTSTRAP.md" -BlockName "BOOTSTRAP-PROMPT" -Body $bootstrapBody -DefaultTitle "FleetVision New Chat Bootstrap"

    $inventoryBody = @"
## Inventory metadata

- Generated: ``$timestamp``
- Project root: ``$($State.ProjectRoot)``
- Remote: ``$($State.RemoteUrl)``
- Branch: ``$($State.Branch)``
- Local HEAD: ``$($State.LocalHead)``
- ``origin/main``: ``$($State.OriginMain)``
- GitHub remote HEAD: ``$($State.GitHubRemoteHead)``
- Local/origin divergence: ``$($State.LocalVsOrigin)``
- Tracked files: **$($State.TrackedFileCount)**
- Tracked Markdown files: **$($State.TrackedMarkdownFiles.Count)**
- Worktree classification: **$($State.StatusClassification)**
- Worktree status before Apply:

````text
$statusDisplay
````

## Top-level directory inventory

$directoryTable

> ``SUMMARY_ONLY`` means the directory was discovered but not recursively counted in targeted mode. Run Audit with ``-IncludeLargeDirectoryInventory`` for recursive counts of dataset/output-heavy directories.

## Tracked Markdown inventory

$markdownTable

## Governance-file allowlist

$($ManagedRelativePaths | ForEach-Object { "- ``$_``" } | Out-String)
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/PROJECT_INVENTORY.md" -BlockName "GENERATED-INVENTORY" -Body $inventoryBody -DefaultTitle "FleetVision Project Inventory"

    $phaseLogBody = @"
## $GovernanceGate — Scheme C migration

- Timestamp: ``$timestamp``
- Technical Phase retained: **$TechnicalPhase**
- Outcome: **PASS after commit/push remote verification**
- Classification: **$GovernanceClassification**
- Base commit: ``$($State.LocalHead)``
- Base commit subject: **$($State.CommitSubject)**
- Scope: governance Markdown, project inventory, new-chat bootstrap, and repeatable governance script
- Excluded: datasets, canonical annotations, Registry, model artifacts, training artifacts, protected external assets
- Verification requirement: only allowlisted governance paths may be staged; final local HEAD, ``origin/main``, and GitHub remote HEAD must match
"@
    Set-ManagedBlock -RelativePath "docs/00_project_management/phase_logs/PHASE_04_5_LOG.md" -BlockName "GOV-C-01" -Body $phaseLogBody -DefaultTitle "FleetVision Phase 04.5 Log"

    $sourceScript = $ScriptSourcePath
    if ([string]::IsNullOrWhiteSpace($sourceScript) -or -not (Test-Path -LiteralPath $sourceScript -PathType Leaf)) {
        throw "Cannot resolve the current script path for repository installation."
    }

    $installedScript = Join-Path $ProjectRoot "scripts\maintenance\project_state_governance.ps1"
    $installedDir = Split-Path -Parent $installedScript
    New-Item -ItemType Directory -Path $installedDir -Force | Out-Null
    Copy-Item -LiteralPath $sourceScript -Destination $installedScript -Force
}

function Get-ChangedPaths {
    $result = Invoke-Git -Arguments @("status", "--porcelain=v1", "--untracked-files=all")
    $paths = New-Object System.Collections.Generic.List[string]
    if ([string]::IsNullOrWhiteSpace($result.Text)) {
        return @()
    }

    foreach ($line in @($result.Text -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.Length -lt 4) { continue }
        $pathPart = $line.Substring(3)
        if ($pathPart -match " -> ") {
            $pathPart = ($pathPart -split " -> ")[-1]
        }
        $paths.Add((Normalize-RepoRelativePath $pathPart))
    }
    return @($paths.ToArray() | Sort-Object -Unique)
}

function Assert-OnlyManagedChanges {
    $changed = Get-ChangedPaths
    $allowed = @(
        $ManagedRelativePaths |
        ForEach-Object {
            Normalize-RepoRelativePath $_
        }
    )

    $unexpected = New-Object System.Collections.Generic.List[string]
    $managedChanged = New-Object System.Collections.Generic.List[string]

    foreach ($path in $changed) {
        # 受保護 external_assets 原本就是 untracked。
        # 不將其列入治理文件的實際變更數量。
        if (
            $path -eq $ProtectedUntrackedPath -or
            $path.StartsWith($ProtectedUntrackedPath + "/")
        ) {
            continue
        }

        if ($allowed -notcontains $path) {
            $unexpected.Add($path)
        }
        else {
            $managedChanged.Add($path)
        }
    }

    if ($unexpected.Count -gt 0) {
        throw (
            "Changes outside the governance allowlist were detected:`n{0}" `
            -f ($unexpected -join "`n")
        )
    }

    $forbiddenPatterns = @(
        "^dataset/01_raw(/|$)",
        "canonical",
        "registry",
        "^outputs/metadata/external_assets(/|$)"
    )

    foreach ($path in $changed) {
        foreach ($pattern in $forbiddenPatterns) {
            if (
                $path -match $pattern -and
                -not (
                    $path -eq $ProtectedUntrackedPath -or
                    $path.StartsWith($ProtectedUntrackedPath + "/")
                )
            ) {
                throw "Forbidden governed asset appears in changed paths: $path"
            }
        }
    }

    return $managedChanged.ToArray()
}

function Verify-GovernanceFiles {
    $requiredMarkers = [ordered]@{
        "AGENTS.md" = "FLEETVISION-MANAGED:GOVERNANCE-CONTRACT:BEGIN"
        "PROJECT_CONTEXT_BRIEF.md" = "FLEETVISION-MANAGED:SOURCE-OF-TRUTH:BEGIN"
        "docs/00_project_management/START_HERE.md" = "FLEETVISION-MANAGED:STARTUP-PROTOCOL:BEGIN"
        "docs/00_project_management/PROJECT_STATUS.md" = "FLEETVISION-MANAGED:CURRENT-STATE:BEGIN"
        "docs/00_project_management/MASTER_PHASE_MAP.md" = "FLEETVISION-MANAGED:CURRENT-CHECKPOINT:BEGIN"
        "docs/00_project_management/WORKFLOW_GOVERNANCE.md" = "FLEETVISION-MANAGED:SCHEME-C:BEGIN"
        "docs/00_project_management/PROTECTED_ASSETS.md" = "FLEETVISION-MANAGED:ASSET-REGISTER:BEGIN"
        "docs/00_project_management/DECISION_LOG.md" = "FLEETVISION-MANAGED:DEC-GOV-2026-0713-01:BEGIN"
        "docs/00_project_management/HANDOFF_CURRENT.md" = "FLEETVISION-MANAGED:CURRENT-HANDOFF:BEGIN"
        "docs/00_project_management/NEW_CHAT_BOOTSTRAP.md" = "FLEETVISION-MANAGED:BOOTSTRAP-PROMPT:BEGIN"
        "docs/00_project_management/PROJECT_INVENTORY.md" = "FLEETVISION-MANAGED:GENERATED-INVENTORY:BEGIN"
        "docs/00_project_management/phase_logs/PHASE_04_5_LOG.md" = "FLEETVISION-MANAGED:GOV-C-01:BEGIN"
    }

    foreach ($entry in $requiredMarkers.GetEnumerator()) {
        $full = Join-Path $ProjectRoot ($entry.Key -replace "/", "\")
        if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
            throw "Required governance file is missing: $($entry.Key)"
        }
        $content = Get-Content -LiteralPath $full -Raw
        if ($content -notmatch [regex]::Escape($entry.Value)) {
            throw "Required managed marker is missing in $($entry.Key): $($entry.Value)"
        }
    }

    $installed = Join-Path $ProjectRoot "scripts\maintenance\project_state_governance.ps1"
    if (-not (Test-Path -LiteralPath $installed -PathType Leaf)) {
        throw "Installed governance script is missing."
    }
}

function Invoke-AuditMode {
    Assert-ProjectRoot
    $state = Get-RepoState -FetchRemote
    $directoryInventory = Get-DirectoryInventory -Deep:$IncludeLargeDirectoryInventory
    $markdownInventory = Get-MarkdownInventory $state
    $auditFiles = Write-AuditFiles $state $directoryInventory $markdownInventory

    Write-Section "FLEETVISION GOVERNANCE AUDIT RESULT"
    Write-Host "Mode: Audit"
    Write-Host "ProjectRoot: $($state.ProjectRoot)"
    Write-Host "Branch: $($state.Branch)"
    Write-Host "LocalHead: $($state.LocalHead)"
    Write-Host "OriginMain: $($state.OriginMain)"
    Write-Host "GitHubRemoteHead: $($state.GitHubRemoteHead)"
    Write-Host "CommitSubject: $($state.CommitSubject)"
    Write-Host "FetchSuccess: $($state.FetchSuccess)"
    Write-Host "StatusClassification: $($state.StatusClassification)"
    Write-Host "TrackedFileCount: $($state.TrackedFileCount)"
    Write-Host "TrackedMarkdownCount: $($state.TrackedMarkdownFiles.Count)"
    Write-Host "ProtectedUntrackedSeen: $($state.ProtectedUntrackedSeen)"
    Write-Host "UnexpectedStatusCount: $($state.UnexpectedStatusLines.Count)"
    Write-Host "AuditJson: $($auditFiles.JsonPath)"
    Write-Host "AuditText: $($auditFiles.TextPath)"

    if ($state.Branch -eq "main" -and
        $state.FetchSuccess -and
        $state.GitHubRemoteReachable -and
        $state.LocalHead -eq $state.OriginMain -and
        $state.LocalHead -eq $state.GitHubRemoteHead -and
        $state.StatusClassification -ne "UNEXPECTED_CHANGES") {
        Write-Host "Classification: GOVERNANCE_MIGRATION_AUDIT_PASS"
    }
    else {
        Write-Host "Classification: GOVERNANCE_MIGRATION_AUDIT_BLOCKED"
    }
    Write-Host "===== END RESULT ====="
}

function Invoke-ApplyMode {
    Assert-ProjectRoot
    $state = Get-RepoState -FetchRemote
    Assert-SafeSynchronizedState -State $state -RequireExpectedHead

    $backupRoot = Backup-ManagedFiles
    $directoryInventory = Get-DirectoryInventory -Deep:$IncludeLargeDirectoryInventory
    $markdownInventory = Get-MarkdownInventory $state

    Apply-GovernanceDocuments -State $state -DirectoryInventory $directoryInventory -MarkdownInventory $markdownInventory
    $changed = Assert-OnlyManagedChanges
    Verify-GovernanceFiles

    Write-Section "FLEETVISION GOVERNANCE APPLY RESULT"
    Write-Host "Mode: Apply"
    Write-Host "BaseHead: $($state.LocalHead)"
    Write-Host "BackupRoot: $backupRoot"
    Write-Host "ChangedPathCount: $($changed.Count)"
    foreach ($path in $changed) {
        Write-Host "Changed: $path"
    }
    Write-Host "ProtectedAssetMutation: NONE"
    Write-Host "CommitPerformed: NO"
    Write-Host "PushPerformed: NO"
    Write-Host "Classification: GOVERNANCE_DOCUMENTS_APPLIED_PENDING_VERIFY"
    Write-Host "===== END RESULT ====="
}

function Invoke-VerifyMode {
    Assert-ProjectRoot
    $state = Get-RepoState -FetchRemote
    if ($state.Branch -ne "main") {
        throw "Verify requires branch main."
    }
    if ($state.LocalHead -ne $state.OriginMain -or $state.LocalHead -ne $state.GitHubRemoteHead) {
        throw "Verify requires the pre-commit base HEAD to remain synchronized with remote."
    }

    Verify-GovernanceFiles
    $changed = Assert-OnlyManagedChanges

    if ($changed.Count -eq 0) {
        throw "No governance changes found to verify."
    }

    Write-Section "FLEETVISION GOVERNANCE VERIFY RESULT"
    Write-Host "Mode: Verify"
    Write-Host "BaseHead: $($state.LocalHead)"
    Write-Host "ChangedPathCount: $($changed.Count)"
    Write-Host "AllowlistCheck: PASS"
    Write-Host "RequiredFilesAndMarkers: PASS"
    Write-Host "ProtectedAssetMutation: NONE"
    Write-Host "Classification: GOVERNANCE_DOCUMENTS_VERIFIED_READY_TO_COMMIT"
    Write-Host "===== END RESULT ====="
}

function Invoke-CommitPushMode {
    Assert-ProjectRoot
    $state = Get-RepoState -FetchRemote
    Assert-SafeSynchronizedState -State $state -RequireExpectedHead -AllowManagedChanges
    Verify-GovernanceFiles
    $changed = Assert-OnlyManagedChanges

    if ($changed.Count -eq 0) {
        throw "No governance changes found to commit."
    }

    foreach ($relative in $ManagedRelativePaths) {
        $full = Join-Path $ProjectRoot ($relative -replace "/", "\")
        if (Test-Path -LiteralPath $full -PathType Leaf) {
            $null = Invoke-Git -Arguments @("add", "--", $relative)
        }
    }

    $stagedResult = Invoke-Git -Arguments @("diff", "--cached", "--name-only")
    $staged = @()
    if (-not [string]::IsNullOrWhiteSpace($stagedResult.Text)) {
        $staged = @($stagedResult.Text -split "`r?`n" | Where-Object { $_ -ne "" } | ForEach-Object {
            Normalize-RepoRelativePath $_
        })
    }

    $allowed = @($ManagedRelativePaths | ForEach-Object { Normalize-RepoRelativePath $_ })
    $unexpectedStaged = @($staged | Where-Object { $allowed -notcontains $_ })
    if ($unexpectedStaged.Count -gt 0) {
        $null = Invoke-Git -Arguments @("reset")
        throw ("Unexpected staged paths detected; staging was reset:`n{0}" -f ($unexpectedStaged -join "`n"))
    }

    if ($staged -contains $ProtectedUntrackedPath -or
        @($staged | Where-Object { $_.StartsWith($ProtectedUntrackedPath + "/") }).Count -gt 0) {
        $null = Invoke-Git -Arguments @("reset")
        throw "Protected external-assets path was staged; staging was reset."
    }

    $commit = Invoke-Git -Arguments @(
        "commit",
        "-m",
        "docs(governance): adopt repository-backed project state"
    )
    $newHead = (Invoke-Git -Arguments @("rev-parse", "HEAD")).Text.Trim()

    $push = Invoke-Git -Arguments @("push", "origin", "main")
    $fetch = Invoke-Git -Arguments @("fetch", "origin", "--prune")
    $finalState = Get-RepoState
    $finalStatus = Get-StatusAssessment

    if ($finalState.LocalHead -ne $newHead) {
        throw "Local HEAD changed unexpectedly after commit."
    }
    if ($finalState.LocalHead -ne $finalState.OriginMain) {
        throw "Post-push local HEAD and origin/main differ."
    }
    if (-not $finalState.GitHubRemoteReachable -or
        $finalState.LocalHead -ne $finalState.GitHubRemoteHead) {
        throw "Post-push GitHub remote HEAD verification failed."
    }
    if ($finalStatus.Classification -eq "UNEXPECTED_CHANGES") {
        throw ("Unexpected final worktree changes:`n{0}" -f ($finalStatus.UnexpectedLines -join "`n"))
    }

    Write-Section "FLEETVISION GOVERNANCE COMMIT/PUSH RESULT"
    Write-Host "Mode: CommitPush"
    Write-Host "BaseHead: $($state.LocalHead)"
    Write-Host "NewHead: $newHead"
    Write-Host "OriginMain: $($finalState.OriginMain)"
    Write-Host "GitHubRemoteHead: $($finalState.GitHubRemoteHead)"
    Write-Host "StagedPathCount: $($staged.Count)"
    Write-Host "FinalStatusClassification: $($finalStatus.Classification)"
    Write-Host "ProtectedExternalAssetsStaged: NO"
    Write-Host "Classification: $GovernanceClassification"
    Write-Host "===== END RESULT ====="
}

try {
    switch ($Mode) {
        "Audit"      { Invoke-AuditMode }
        "Apply"      { Invoke-ApplyMode }
        "Verify"     { Invoke-VerifyMode }
        "CommitPush" { Invoke-CommitPushMode }
        default      { throw "Unsupported mode: $Mode" }
    }
}
catch {
    Write-Host ""
    Write-Host "===== FLEETVISION GOVERNANCE FAILURE ====="
    Write-Host "Mode: $Mode"
    Write-Host "Classification: GOVERNANCE_MIGRATION_FAILED_OR_BLOCKED"
    Write-Host "Error: $($_.Exception.Message)"
    Write-Host "Script: $($_.InvocationInfo.ScriptName)"
    Write-Host "Line: $($_.InvocationInfo.ScriptLineNumber)"
    Write-Host "===== END FAILURE ====="
    exit 1
}




