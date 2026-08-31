#!/usr/bin/env python3
"""
生成 Sileo/Cydia 仓库索引（GitHub Pages 自建源用）。

用法:
    python3 gen-repo.py [packages_dir]

在 packages_dir 下扫描 *.deb，生成:
    Packages / Packages.bz2 / Packages.xz / Release

然后:
    git add -A && git commit -m "update packages" && git push
    （GitHub Pages 会在 ~1 分钟后自动发布新索引）
"""
import os, sys, glob, io, time, bz2, lzma, hashlib, tarfile

DEFAULT_PKGDIR = "packages"


def read_control(deb_path: str) -> str:
    """从 .deb (ar 归档) 里解出 control 字段文本。"""
    with open(deb_path, "rb") as f:
        data = f.read()
    off = 8  # ar 头部之后
    while off + 60 <= len(data):
        hdr = data[off:off + 60]
        name = hdr[0:16].decode("utf-8", "replace").strip()
        try:
            size = int(hdr[48:58].decode().strip())
        except ValueError:
            break
        body = data[off + 60: off + 60 + size]
        if name.startswith("control.tar"):
            t = tarfile.open(fileobj=io.BytesIO(body))
            for m in t.getmembers():
                if m.name.endswith("/control"):
                    return t.extractfile(m).read().decode("utf-8", "replace")
        off += 60 + size + (size % 2)
    return ""


def main() -> None:
    pkgdir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PKGDIR
    debs = sorted(glob.glob(os.path.join(pkgdir, "*.deb")))
    if not debs:
        sys.exit(f"在 {pkgdir}/ 下没有找到 .deb")

    blocks = []
    for deb in debs:
        ctrl = read_control(deb)
        if not ctrl:
            print(f"!! 无法读取 control: {deb}")
            continue
        with open(deb, "rb") as f:
            raw = f.read()
        rel = "./" + deb.replace(os.sep, "/")
        ctrl = ctrl.rstrip() + "\n" + "\n".join([
            f"Filename: {rel}",
            f"Size: {len(raw)}",
            f"SHA256: {hashlib.sha256(raw).hexdigest()}",
            f"MD5sum: {hashlib.md5(raw).hexdigest()}",
        ]) + "\n\n"
        blocks.append(ctrl)
        print(f"  + {deb}  ({len(raw):,} B)")

    pkgs = "".join(blocks)
    open("Packages", "w").write(pkgs)
    open("Packages.bz2", "wb").write(bz2.compress(pkgs.encode()))
    open("Packages.xz", "wb").write(lzma.compress(pkgs.encode()))

    release = "\n".join([
        "Origin: NoBTAudioReconnect",
        "Label: NoBTAudioReconnect",
        "Suite: stable",
        "Version: 1.0",
        "Codename: nbt",
        "Architectures: iphoneos-arm64",
        "Components: main",
        f"Date: {time.strftime('%a, %d %b %Y %H:%M:%S %z')}",
        "Description: Block BTAudioHALPlugin.bundle to stop launchd busy loop (iOS 16.x)",
        "",
    ])
    open("Release", "w").write(release)
    print(f"\n已生成: Packages / Packages.bz2 / Packages.xz / Release（共 {len(blocks)} 个包）")
    print("未签名。如需签名: gpg -abs -o Release.gpg Release")


if __name__ == "__main__":
    main()
