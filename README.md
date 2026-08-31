# NoBTAudioReconnect

> 禁止 iOS 系统组件 `BTAudioHALPlugin.bundle` 在《鸣潮》/《异环》进程内加载，解决 iOS 16.5.1 上 `launchd (PID 1)` 单核 100% 的问题。
>
> A rootless tweak that stops iOS's Bluetooth-audio HAL plugin (`BTAudioHALPlugin.bundle`) from loading into
> *Wuthering Waves* / *Neverness to Everness*, fixing a `launchd (PID 1)` single-core 100% busy loop on iOS 16.5.1.

## 这是什么 / What this is

在 iPhone SE3 + iOS 16.5.1 上，当 App 以特定方式初始化音频（如 `PlayAndRecord` + `AllowBluetooth`）时，CoreAudio 会把系统组件
`/System/Library/Audio/Plug-Ins/HAL/BTAudioHALPlugin.bundle` 加载进 **App 进程**。该插件随即反复调用
`xpc_connection_create_mach_service("com.apple.BTAudioHALPlugin.xpc")`（实测 **约 6000 次/秒**）以连接 `bluetoothd`，
但第三方 App 的沙箱**必然拒绝**该查询（`error 159: Sandbox restriction`），插件收到失败后**立即重开新连接、无退避**，
形成无上界循环。每次查询都让 `launchd` 做一次沙箱策略计算 → **PID 1 单核饱和**，设备发热、界面卡顿。
系统统一日志可看到 `418721 duplicate reports` 的同一条拒绝消息。

本插件 hook `dlopen`，把路径含 `BTAudioHALPlugin` 的加载直接返回 NULL，**让插件根本进不了进程**，
从源头掐断循

如果你的设备没有 launchd 问题，此插件应当不起作用。

插件仅在本人 iPhone SE3 + iOS 16.5.1 这台手机上测试可用，不保证其他设备和系统版本的可用性。

## 效果 / Effect

- 实测（鸣潮 3.5.3 / iPhone SE3 / iOS 16.5.1）：`launchd` 占用从 **~88% 单核回落到近 0%**，游戏正常进入。
- 对照实验：hook 掉插件加载前后，launchd 占用 88% → 0%，证明插件加载 = 问题必要且充分条件。
- 副作用：蓝牙音频 HAL 不再加载（蓝牙音频路由可能失效）；扬声器 / 有线耳机 / 普通音频不受影响。

## 兼容性 / Compatibility

- iOS 16.5.1 **rootless** 越狱。
- RootHide 半越狱经过 RootHide Patcher 转换后可用。
- 需要 **ElleKit**（提供 `mobilesubstrate` 兼容层，`Depends: mobilesubstrate`）
- 仅注入 `com.kurogame.mingchao`（鸣潮国服）与 `com.pwrd.yh.ios`（异环国服）
- 架构：`iphoneos-arm64`

## 安装 / Install

```bash
# 方式一：deb 直装（rootless 路径）
ssh root@<device> "dpkg -i /var/mobile/Documents/NoBTAudioReconnect.deb"
```

```bash
# 方式二：Sileo 添加本仓库源后搜索 NoBTAudioReconnect
https://mclyx.github.io/NoBTAudioReconnect/
```

```bash
# 卸载
dpkg -r com.local.nobtaudioreconnect
```

## ⚠️ 免责声明 / Disclaimer

**仅供测试与研究使用。** 使用本插件可能造成：

- 功能异常（如蓝牙音频路由失效、语音相关功能不可用）；
- 游戏反作弊系统（腾讯ACE）检测到注入/调试行为，可能导致**账号/IP/设备封禁**；
- 与当前系统/游戏版本不兼容导致的崩溃或其它问题。

**使用本项目出现的任何问题后果自负。** 本项目与《鸣潮》（库洛游戏）、《异环》（完美世界）及 Apple 均无任何关联，
不提供任何形式的担保。使用即代表你已阅读并同意以上条款。

## 构建 / Build

需要 [Theos](https://theos.dev)（Linux 亦可用）与 `ldid`。

```bash
git clone --recursive https://github.com/theos/theos.git ~/theos
# ... 安装工具链与 iPhoneOS16.5.sdk（见 Theos 文档）...
export THEOS=~/theos
make package FINALPACKAGE=1   # 产物在 packages/
```

## 自建 Sileo/Cydia 源（GitHub Pages） / Hosting a repo on GitHub Pages

GitHub Pages 可以当一个 Sileo/Cydia 仓库：仓库本质上就是一个静态目录，包含 `.deb` 文件和一个 `Packages` 索引。

1. 把本仓库推到 GitHub（公开仓库），然后在 **Settings → Pages → Source: Deploy from a branch → main / (root)** 开启 Pages。
2. 每次更新 `packages/*.deb` 后，运行索引生成脚本：
   ```bash
   python3 gen-repo.py        # 生成 Packages / Packages.bz2 / Packages.xz / Release
   ```
3. 提交并推送，等 Pages 构建完成（约 1 分钟）。
4. 在 Sileo 里添加源：`https://<你的用户名>.github.io/<仓库名>/`

说明：

- 未签名的源在 Sileo 会提示不受信任，个人使用可直接确认；如需签名，用 GPG 对 `Release` 签名生成 `Release.gpg`。
- 本仓库的包架构是 `iphoneos-arm64`（rootless），请用 Sileo（iOS 16 rootless 无 Cydia）。
- RootHide 半越狱请转换后安装。

## 原理细节（给好奇的人）

- 模块身份：`4179342D-0A9E-3540-89FC-6A1115E9FD58` = `/System/Library/Audio/Plug-Ins/HAL/BTAudioHALPlugin.bundle`
  （arm64, MH_BUNDLE, 597,472 B，链接 CoreBluetooth / AudioServerDriver / CoreAudio 等 Apple 蓝牙音频栈）。

## 版本历史 / Changelog

| 版本 | 说明 |
|---|---|
| v0.0.1–0.0.2 | 初版：丢弃 BTAudioHALPlugin 队列的 `dispatch_after`。**实测无效**（循环不走该路径），仅存档 |
| v0.0.3 | 诊断版：hook `xpc_connection_create_mach_service`，抓到循环本体 ~6000 次/秒 |
| v0.0.4 | 对照实验版：hook `dlopen` 禁止插件加载 → launchd 回落近 0%，证明因果 |
| **v0.0.5** | 正式版：KILL_LOAD 静默化，日志严格限流，不再刷屏 |

## License

MIT © 2026 mcLYX
