"""Prepare the pinned official Android shell for this fork's debug artifact."""
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[2]
shell = root / "android-shell"
version = json.loads((root / "app/package.json").read_text())["version"]
p = shell / "build.gradle"
s = p.read_text()
import re
s = re.sub(r'siyuanVersionName = "[^"]+"', f'siyuanVersionName = "{version}-selfhost-test"', s)
s = "\n".join(line for line in s.splitlines() if "maven.aliyun.com" not in line) + "\n"
p.write_text(s)
shutil.copyfile(shell / "signings.templates.gradle", shell / "signings.gradle")
(shell / "app/libs").mkdir(parents=True, exist_ok=True)
shutil.copyfile(root / "kernel/kernel.aar", shell / "app/libs/kernel.aar")
assets = shell / "app/src/main/assets"
assets.mkdir(parents=True, exist_ok=True)
shutil.copyfile(root / "ui-artifact/selfhost-ui.zip", assets / "app.zip")
