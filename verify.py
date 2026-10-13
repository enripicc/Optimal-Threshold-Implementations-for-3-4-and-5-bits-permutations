#!/usr/bin/env python3
"""Inspect and verify CSV witnesses in the adjacent 3bit, 4bit and 5bit folders.

Run python3 verify.py --help for examples. Requires only Python 3.10+.

Each component is Base64-encoded packed data: n bits per output, LSB first.
Component j omits input share j; the remaining shares index its table in
increasing order, with the lowest-numbered share in the least significant bits.
Non-completeness is guaranteed by this representation.
"""

import argparse
import base64
import csv
from functools import reduce
from operator import xor
from pathlib import Path

def check(condition, message):
    if not condition:
        raise ValueError(message)


def degree(table):
    """Compute the vectorial algebraic degree by the binary Moebius transform."""
    coefficients = bytearray(table)
    for bit in range((len(table) - 1).bit_length()):
        half = 1 << bit
        for start in range(0, len(table), 2 * half):
            for i in range(start + half, start + 2 * half):
                coefficients[i] ^= coefficients[i - half]
    return max((i.bit_count() for i, value in enumerate(coefficients) if value), default=0)


def decode_component(text, n, entries):
    data = base64.b64decode(text, validate=True)
    check(len(data) * 8 == n * entries, "Incorrect component table size")
    table = bytearray(entries)
    for i in range(entries):
        byte, shift = divmod(n * i, 8)
        value = data[byte] >> shift
        if shift + n > 8:
            value |= data[byte + 1] << (8 - shift)
        table[i] = value & ((1 << n) - 1)
    return table


def read_row(path):
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    check(len(rows) == 1, "Expected one implementation per CSV")
    return rows[0]


def load_ti(path):
    row = read_row(path)
    check((row["format_version"], row["packing"], row["text_encoding"])
          == ("1", "lsb0", "base64"), "Unsupported table encoding")

    n, s = int(row["n_bits"]), int(row["shares"])
    check(n in (3, 4, 5) and s in (2, 3, 4), "Invalid width or share count")
    q = 1 << n
    target = bytes.fromhex(row["sbox_hex_bytes"])
    check(sorted(target) == list(range(q)), "Target is not a permutation")
    target_degree = degree(target)
    check(target_degree == int(row["target_degree"]), "Incorrect target degree")
    check(s == target_degree + 1, "Expected deg(F) + 1 shares")

    entries = q ** (s - 1)
    check(int(row["entries_per_component"]) == entries, "Incorrect table length")
    check(all(row[f"component_{j+1}"] == "" for j in range(s, 4)),
          "Unexpected unused component data")
    return row, n, s, target


def verify(path):
    row, n, s, target = load_ti(path)
    q = 1 << n
    entries = q ** (s - 1)

    tables = [decode_component(row[f"component_{j+1}"], n, entries) for j in range(s)]
    component_degrees = [degree(table) for table in tables]
    check(component_degrees == list(map(int, row["component_degrees"].split())),
          "Incorrect component degrees")

    # Fix shares 2,...,s, then vary share 1. This visits all q**s shared inputs.
    # A byte per possible output records bijectivity, without storing the full map.
    states = q ** s
    seen = bytearray(states)
    for tail in range(entries):
        y0 = tables[0][tail]  # Component 1 omits input share 1.
        tail_secret = 0
        blocks = []
        for j in range(1, s):
            shift = n * (j - 1)
            tail_secret ^= (tail >> shift) & (q - 1)
            # Delete share j+1 from the tail; share 1 indexes the resulting block.
            lower = tail & ((1 << shift) - 1)
            upper = tail >> (shift + n)
            start = q * (lower | (upper << shift))
            blocks.append(tables[j][start:start + q])

        for a, values in enumerate(zip(*blocks)):
            combined, output = y0, 0
            for value in reversed(values):
                combined ^= value
                output = (output << n) | value
            output = (output << n) | y0
            if combined != target[a ^ tail_secret]:
                raise ValueError(f"Correctness failed at packed input {a | (tail << n)}")
            if seen[output]:
                raise ValueError(f"Uniformity failed: repeated packed output {output}")
            seen[output] = 1
    # There are equally many inputs and outputs, so no repeats implies bijectivity.
    return states


def select_files(selectors, bits):
    """Select by class name or CSV path; no selectors means the whole collection."""
    root = Path(__file__).resolve().parent
    available = [p for n in (3, 4, 5) for p in (root / f"{n}bit").glob("*.csv")]
    if selectors:
        catalogue = {read_row(p)["class_name"].upper(): p for p in available}
        files = []
        for name in selectors:
            path = Path(name)
            if not path.is_file():
                path = root / name
            if not path.is_file():
                path = catalogue.get(name.upper())
            check(path is not None and path.is_file(),
                  f"Cannot find {name!r}. Use a class name such as Q4_300 or a CSV path; try --list.")
            files.append(path.resolve())
    else:
        for n in (bits,) if bits else (3, 4, 5):
            check(any(p.parent.name == f"{n}bit" for p in available),
                  f"No CSV files in {root / f'{n}bit'}")
        files = available
    files = sorted(set(files), key=lambda p: (int(read_row(p)["n_bits"]),
                                              int(read_row(p)["class_index"])))
    if bits:
        files = [p for p in files if int(read_row(p)["n_bits"]) == bits]
    check(files, "No implementations match this selection")
    return files


def show(path):
    row, n, s, target = load_ti(path)
    print(f"\n{row['class_name']}: {n} bits, target degree {row['target_degree']}, {s} shares")
    print(f"Recorded component degrees: {row['component_degrees']}")
    print("Target truth table (outputs for inputs 0, 1, ...):")
    print("Decimal: " + " ".join(str(int(y)) for y in target))
    print("Hex:     " + " ".join(f"{int(y):02X}" for y in target))
    print(f"{'x':>3}  {'F(x)':>4}  {'input bits':>{n}}  output bits")
    for x, y in enumerate(target):
        print(f"{x:3d}  {int(y):4d}  {x:0{n}b}  {int(y):0{n}b}")
    print("Use the default verification command to check all TI properties.")


def evaluate(path, inputs):
    row, n, s, target = load_ti(path)
    check(len(inputs) == s, f"{row['class_name']} needs exactly {s} input shares")
    check(all(0 <= x < (1 << n) for x in inputs), f"Each share must be in 0..{(1 << n)-1}")
    outputs = []
    for j in range(s):
        table = decode_component(row[f"component_{j+1}"], n, 1 << (n * (s - 1)))
        remaining = [x for k, x in enumerate(inputs) if k != j]
        index = sum(x << (n * k) for k, x in enumerate(remaining))
        outputs.append(int(table[index]))
    secret, result = reduce(xor, inputs), reduce(xor, outputs)
    print(f"{row['class_name']}: input shares {inputs}; output shares {outputs}")
    print(f"Input XOR = {secret}; output XOR = {result}; F({secret}) = {int(target[secret])}")
    check(result == int(target[secret]), "Correctness failed for these inputs")
    print("This evaluates one sharing; run the default command for exhaustive verification.")


def export_targets(files, destination):
    """Write one ordinary CSV row per class, with decimal target outputs."""
    check(not destination.exists(), f"{destination} already exists; choose another output filename")
    rows = []
    for path in files:
        row, n, s, target = load_ti(path)
        rows.append([row["class_name"], n, row["class_index"], row["target_degree"],
                     s, row["component_degrees"], " ".join(str(int(y)) for y in target)])
    with destination.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["class_name", "n_bits", "class_index", "target_degree", "shares",
                         "recorded_component_degrees", "target_outputs_decimal"])
        writer.writerows(rows)
    print(f"Exported {len(rows)} target truth tables to {destination} (input order 0, 1, ...).")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect or exhaustively verify the supplied threshold implementations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 verify.py                         Verify every TI
  python3 verify.py Q4_300                  Verify one class
  python3 verify.py Q3_1 C5_114              Verify selected classes
  python3 verify.py 4bit/ti_4_300.csv        Verify a CSV file
  python3 verify.py --bits 5                Verify all five-bit TIs
  python3 verify.py --list                  List available classes and recorded degrees
  python3 verify.py Q4_300 --show           Display the target truth table
  python3 verify.py --bits 3 --show         Display all three-bit target tables
  python3 verify.py Q4_300 --evaluate 3 7 9  Evaluate one input sharing
  python3 verify.py --export targets.csv    Export all target truth tables

Share values may be decimal, hexadecimal (0x...), or binary (0b...).
The data folders are located relative to this script, not the working directory.
Listing, displaying, evaluating and exporting do not run exhaustive verification.""")
    parser.add_argument("classes", nargs="*", help="Class names or CSV paths; default: all")
    parser.add_argument("--bits", type=int, choices=(3, 4, 5), help="Filter by input width")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--list", action="store_true", help="List available classes")
    actions.add_argument("--show", action="store_true", help="Show target truth tables")
    actions.add_argument("--evaluate", nargs="+", type=lambda x: int(x, 0), metavar="SHARE",
                         help="Evaluate a single class on the supplied input shares")
    actions.add_argument("--export", type=Path, metavar="CSV", help="Export target truth tables")
    args = parser.parse_args()
    try:
        files = select_files(args.classes, args.bits)
        if args.list:
            print("Class       Bits  Degree  Shares  Recorded component degrees")
            for path in files:
                row = read_row(path)
                print(f"{row['class_name']:<11} {row['n_bits']:>4}  {row['target_degree']:>6}"
                      f"  {row['shares']:>6}  {row['component_degrees']}")
            print(f"{len(files)} implementations")
        elif args.show:
            for path in files:
                show(path)
        elif args.evaluate is not None:
            check(len(files) == 1, "Select exactly one class with --evaluate")
            evaluate(files[0], args.evaluate)
        elif args.export:
            export_targets(files, args.export)
        else:
            total = 0
            for i, path in enumerate(files, 1):
                try:
                    total += verify(path)
                except (ValueError, KeyError, TypeError, OSError) as error:
                    raise ValueError(f"{path.name}: {error}") from error
                print(f"[{i}/{len(files)}] PASS {read_row(path)['class_name']}", flush=True)
            print(f"PASS: {len(files)} implementations; {total:,} shared inputs")
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
