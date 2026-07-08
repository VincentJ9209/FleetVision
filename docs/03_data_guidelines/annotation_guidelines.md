# 車損標註規則

## 第一版類別

```text
0: damage
```

## 標註方式

使用 bounding box 框住可見車損區域。

## 應標註

- 刮傷
- 擦傷
- 凹陷
- 撞傷
- 掉漆
- 破裂
- 明顯車身外觀損傷

## 不標註或暫不標註

- 反光
- 陰影
- 車門縫
- 髒污，除非專案定義為異常
- 水痕，除非專案定義為異常
- 模糊到無法確認的痕跡

## 不確定案例

不確定時請標記為 `review_required`，不要強行標註。

## 版本管理

每一次標註修正都應建立版本，例如：

```text
dataset/04_annotations/annotation_versions/v001_damage_bbox/
dataset/04_annotations/annotation_versions/v002_damage_bbox/
```
