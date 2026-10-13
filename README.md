This repository contains **401 threshold implementations (TIs)** of nonlinear
three-, four-, and five-bit permutations. An implementation of a target
permutation of algebraic degree `t` uses `t + 1` shares: three for a quadratic
permutation and four for a cubic permutation.

The associated paper will be linked here once it is public on the
[IACR Cryptology ePrint Archive](https://eprint.iacr.org/).

| Size | Quadratic targets: 3 shares | Cubic targets: 4 shares | Total |
|---|---:|---:|---:|
| 3 bits | 2 / 3 | — | 2 / 3 |
| 4 bits | 6 / 6 | 295 / 295 | 301 / 301 |
| 5 bits | 53 / 75 | 45 / 57 | 98 / 132 |
| **Total** | **61 / 84** | **340 / 352** | **401 / 436** |

Each entry gives the number of classes with a supplied TI out of the nonlinear
affine-equivalence classes considered. For three and four bits, these are all
nonlinear permutation classes [1]. For five bits, they are the 75 quadratic
classes and the 57 cubic inverse classes in [2].

## Getting started

Open a terminal in the repository directory. On Linux or macOS:

```sh
python3 verify.py --help
python3 verify.py
```

On Windows:

```powershell
py verify.py --help
py verify.py
```

## Commands

| Task | Command |
|---|---|
| Verify every supplied TI | `python3 verify.py` |
| Verify one class | `python3 verify.py Q4_300` |
| Verify selected classes | `python3 verify.py Q3_1 C5_114` |
| Verify a CSV file | `python3 verify.py 4bit/ti_4_300.csv` |
| Verify all five-bit TIs | `python3 verify.py --bits 5` |
| List available classes and recorded degrees | `python3 verify.py --list` |
| List five-bit classes | `python3 verify.py --bits 5 --list` |
| Display a target truth table | `python3 verify.py Q4_300 --show` |
| Display all three-bit target tables | `python3 verify.py --bits 3 --show` |
| Export all target truth tables | `python3 verify.py --export targets.csv` |
| Export selected target truth tables | `python3 verify.py Q3_1 Q4_300 --export selected.csv` |
| Evaluate a TI on input shares | `python3 verify.py Q4_300 --evaluate 3 7 9` |

Class names are case-insensitive. Input shares may be decimal integers, or use
the prefixes `0x` for hexadecimal and `0b` for binary. Exactly one class must be
selected with `--evaluate`.

For example, evaluating `Q4_300` on the shares `3, 7, 9` gives output shares
`5, 13, 7`. Their XOR is `15`, which equals `F(3 XOR 7 XOR 9) = F(13)`.

`--show` displays the **target permutation's truth table** in decimal,
hexadecimal, and binary. `--export` writes a conventional CSV with one row per
class, including the target outputs `F(0), F(1), ..., F(2^n - 1)` in decimal.
Export commands refuse to overwrite existing files.

Listing, displaying, exporting, and evaluating one sharing do not run
exhaustive verification. To check a TI, run the default verification command
on the desired class or classes. Data folders are located relative to the
script, so the script can also be invoked from another working directory.

## Notation and class numbering

`Qn_i` and `Cn_i` are plain-text forms of $Q_i^n$ and $C_i^n$: `Q` denotes a
quadratic class, `C` a cubic class, `n` the size in bits, and `i` its
affine-equivalence class index. This notation was introduced by Bilgin et al.
[1, Section 2.3].

The three- and four-bit numbers and representatives follow
[1, Appendix A, Tables 7–10]. The five-bit quadratic indices follow the
classification of Božilov, Bilgin, and Şahin [2, Tables 1 and 2].

For five-bit cubic classes, this collection extends the numbering in [2]:
indices `76` through `132` denote the inverses of the quadratic classes listed
in its Table 2, in increasing order of their quadratic indices. Explicitly,
the inverse class of `Q5_j` is labelled:

| Quadratic class index | Label of its inverse class |
|---|---|
| `18 <= j <= 29` | `C5_(j+58)` |
| `31 <= j <= 75` | `C5_(j+57)` |

Thus `C5_76` corresponds to the inverse of `Q5_18`, and `C5_114` to the inverse
of `Q5_57`. This numbering extension is a convention of this collection;
[2] provides the quadratic classification and identifies which inverses are
cubic. Only classes with supplied TI witnesses appear here. The explicit target
truth table in each CSV determines its representative independently of these
labels.

## References

1. B. Bilgin, S. Nikova, V. Nikov, V. Rijmen, and G. Stütz.
   **Threshold Implementations of all 3x3 and 4x4 S-boxes.** CHES 2012,
   pp. 76–91. Extended version: Cryptology ePrint Archive, Report 2012/300.
   [Full version](https://eprint.iacr.org/2012/300).
2. D. Božilov, B. Bilgin, and H. A. Şahin.
   **A Note on 5-bit Quadratic Permutations’ Classification.**
   IACR Transactions on Symmetric Cryptology, 2017(1), pp. 398–404.
   [DOI: 10.13154/tosc.v2017.i1.398-404](https://doi.org/10.13154/tosc.v2017.i1.398-404).
