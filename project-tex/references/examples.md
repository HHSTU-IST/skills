# 公式样例

[`SKILL.md`](../SKILL.md) 的规则表说的是「不写什么、改写成什么」，这里给每个环境的整块写法，照抄即可。独立公式包在 `$$ ... $$` 里（`.tex` 里用 `\[ ... \]`）。

## 多行公式

减少 `\begin{array}` 的用法，按语义挑下面这几种。

### 居中、不编号：gathered

```latex
\begin{gathered}
x_1 = \bigg(1 + \dfrac{3}{100} \bigg) ×10, 000 \\
x_2 = \bigg(1 + \dfrac{3}{100} \bigg) × x_1 = \bigg(1 + \dfrac{3}{100} \bigg)^2×10, 000 \\
…
\end{gathered}
```

### 居中、编号：gather

```latex
\begin{gather}
3x_1^2 + 2x_1x_2 + x_2^2 \\
x_1^2 - 2x_2^2
\end{gather}
```

### 按符号对齐：aligned

```latex
\begin{aligned}
y_1 &= x^2 + 2*x \\
y_2 &= x^3 + x
\end{aligned}
```

### 分段、带条件：cases

```latex
\begin{cases}
y = x^2 + 2*x & x > 0 \\
y = x^3 + x & x ⩽ 0
\end{cases}
```

### 行列式：vmatrix

```latex
\begin{vmatrix}
a + a' & b + b' \\
c & d
\end{vmatrix} =
\begin{vmatrix}
a & b \\
c & d
\end{vmatrix} +
\begin{vmatrix}
a' & b' \\
c & d
\end{vmatrix}
```

### 矩阵：bmatrix

```latex
\begin{bmatrix}
a_{11} & a_{12} & ⋯ & a_{1n} \\
a_{21} & a_{22} & ⋯ & a_{2n} \\
⋮ & ⋮ & ⋱ & ⋮ \\
a_{m1} & a_{m2} & ⋯ & a_{mn}
\end{bmatrix}
```

## 括号

括号尺寸显式写出来，别让引擎去猜。

```latex
A\bigg[\frac{1}{2}\ \frac{1}{3}\ ⋯\ \frac{1}{99}\bigg]
```

`\underset` / `\overset` 两个参数位都写全，空位留空花括号。

```latex
\underset{w}{\mathrm{argmin}}(wx + b)
```

## 记号

```latex
A^{\top}
```

```latex
\lim_{n\to \infty}
```

## 字体

正体、粗体、斜体各只有一个命令。

```latex
θ_\mathrm{MLE} = \underset{θ}{\mathrm{argmax}}\sum_{i=1}^{N}\log p(x_i ∣ θ)
```

## 备注

样例源码里混用了字面量和命令：`×`、`⩽`、`⋯`、`⋮`、`⋱`、`∣` 是直接敲的字符，`\dfrac`、`\bigg`、`\to`、`\infty`、`\begin{gathered}` 是命令。照抄样例；检查脚本不对这些字符作判断，只管规则表里那九行。
