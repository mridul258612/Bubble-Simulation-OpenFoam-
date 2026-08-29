from pathlib import Path
import re


CASE_DIR = Path(__file__).resolve().parent
FIELD_PATTERN = re.compile(
    r"(internalField\s+nonuniform\s+List<scalar>\s+)"
    r"(\d+)(\s*\(\s*)(.*?)(\s*\)\s*;)",
    re.DOTALL,
)
NUMBER_PATTERN = re.compile(
    r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
)


def create_alpha_air(alpha_water_path):
    text = alpha_water_path.read_text()
    match = FIELD_PATTERN.search(text)
    if match is None:
        raise ValueError(f"Unsupported field format: {alpha_water_path}")

    count = int(match.group(2))
    water_values = [float(value) for value in NUMBER_PATTERN.findall(match.group(4))]
    if len(water_values) != count:
        raise ValueError(
            f"Expected {count} values, found {len(water_values)}: "
            f"{alpha_water_path}"
        )

    air_values = [1.0 - value for value in water_values]
    replacement = (
        match.group(1)
        + match.group(2)
        + match.group(3)
        + "\n"
        + "\n".join(f"{value:.12g}" for value in air_values)
        + "\n"
        + match.group(5)
    )
    air_text = text.replace("object      alpha.water;", "object      alpha.air;", 1)
    air_text = FIELD_PATTERN.sub(replacement, air_text, count=1)
    alpha_water_path.with_name("alpha.air").write_text(air_text)


for time_dir in sorted(CASE_DIR.iterdir(), key=lambda path: path.name):
    if not time_dir.is_dir():
        continue
    try:
        float(time_dir.name)
    except ValueError:
        continue

    alpha_water_path = time_dir / "alpha.water"
    if alpha_water_path.exists():
        create_alpha_air(alpha_water_path)
        print(f"Created {time_dir / 'alpha.air'}")