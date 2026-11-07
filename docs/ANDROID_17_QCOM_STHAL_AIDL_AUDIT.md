# PixelExperience-Reborn Android 17 — row 176: Qualcomm Sound Trigger HAL and AudioReach AIDL

**Audited:** 2026-11-07. **Target:** independently built PixelExperience-Reborn AOSP17 for POCO F5 Pro / Redmi K60, `mondrian`, SM8475 / Qualcomm platform family `taro`. We prefer a **newer hardware-compatible Qualcomm source generation** over archived 2022/2023 source, but an arbitrary current branch must not be installed without its entire DSP/audio vendor graph.

## Decision

**Do not enable the historical `vendor/qcom/opensource/audio-hal/st-hal` (C/LSM/GCS) in Android 17.** It is disabled by `Android.mk` when `TARGET_USES_QCOM_AUDIO_AR=true`, builds `sound_trigger.primary.$(TARGET_BOARD_PLATFORM)`, and assumes older `KERNEL_OBJ`/GCS/libgcs/kernel techpack and proprietary audio HAL callback contracts.

Prefer to evaluate the **modern, Qualcomm-derived AudioReach SoundTrigger3 AIDL implementation** from the Sony-hosted `aosp/AUDIO.LA.10.0.r1` source line, together with its matching primary Audio HAL, PAL, AGM, DSP graph services and graph configuration. In particular this modern source is a real **AIDL V1** `ISoundTriggerHw/default` HAL implementation, not merely a PAL-backed legacy `sound_trigger.primary.*.so`.

**No production activation yet.** The independent PE manifest currently has only AOSP17 sources and PE-reviewed host/core forks, **no actual mondrian product, DSP firmware or verified stock vendor audio service**. Stage a strictly nondefault **six-source, pinned, testable** experiment; promote only after hardware and build validation. Keeping the new source outside active `default.xml` is a deliberate safety boundary, not a decision to port the older HAL.

## Immutable source basis

| Branch/repository | SHA (Git tree) | Finding |
| --- | --- | --- |
| Historical PE `vendor_qcom_opensource_audio-hal_st-hal` `seventeen` | `68d8705deab99367a1c4022470feb7a4bf8cc785` (`1f74e1622de15d71d8999e6969932a1f0bce2f4a`), 2023-10-24 | 43-file legacy Sound Trigger C API with GCS/LSM, `sound_trigger.primary.$(TARGET_BOARD_PLATFORM)`, chipset and kernel UAPI coupling |
| PE `vendor_qcom_opensource_audio-hal_st-hal-ar` `seventeen` — next matrix row 177 | `420362bced12aa266fbf73be76ee440b8341829f` (`4e0987fea0b25cc46803456cd8e39c616d7602df`), 2024-01-04 | 10 files, Qualcomm PAL-backed but still legacy `sound_trigger.primary.*` and `sound_trigger_hw_device` |
| Actual selected PE Android17 `hardware_interfaces` port branch | `735e364cbdd00b0d6e4dc33ea0866dbb6d971a11` (`adad11a145a3ecd709642f720a53f5a923fce754`) | Frozen official AOSP17 `android.hardware.soundtrigger3` stable AIDL V1, V2, V3, **V4**; independent PE owner retained |
| Sony-hosted Qualcomm-derived modern SoundTrigger `vendor-qcom-opensource-audio-hal-st-hal-ar`, `aosp/AUDIO.LA.10.0.r1` | `1dcb1275256b3f43b78d342d623870324a831720` (`d47390edeaf35ee6b50d15b88e9f5537f372174e`) | 19-file PAL-backed **SoundTrigger3 AIDL V1** `libsoundtriggerhal.qti` factory and VINTF |
| Modern primary Audio HAL `vendor-qcom-opensource-audio-hal-primary-hal-ar`, same upstream branch | `b071e74ead44a7aecee69969003b902632cd4ab3` (`c78551f4c27dab685e396cd8996c1458b724787d`), 2026-08-04 | Android17 version bump: Audio **Core AIDL V3**, **Effects V4**; `audiohalservice.qti` dynamic factory registration; includes legacy `configs/taro/` example |
| Newer PAL `vendor-qcom-opensource-arpal-lx` | `44e6ad74fd34c390b053bbe19811502c132f007e` (`a1ec1aec66c66d7672fde7f3349bdef852a5d962`) | PAL library and headers |
| Newer AGM `vendor-qcom-opensource-agm` | `7ad4167f2241beefd2a48b9e87453c3a80c5811b` (`6c4eaa800ab4d1f2d584b51ae4e020eb68408c90`) | Audio graph manager |
| Newer AudioReach graphservices `vendor-qcom-opensource-audioreach-graphservices` | `d38796b5d74ff727a5fbd9f10ecbc7f5c0335ff5` (`40286aaa0fbdfad8538496de1096d6b68b6e60a2`) | GPR/ACDB/etc DSP graph implementations |
| Newer AudioReach configuration `vendor-qcom-opensource-audioreach-conf` | `5e90f9e4d6bb790fca0a092d57fdee8572d5b990` (`76314d215f91c4125bc09ea48f6085eee02f3b1e`) | Graph/kv header/config sources |

Sony GitHub is an inspectable mirror of Qualcomm-derived audio source; it does **not** establish current Qualcomm CodeLinaro release authenticity or Xiaomi OEM branch provenance. An alternative recent (2026-09) AOSPA `calcite-8650` source still exports a legacy Soong module `sound_trigger.primary.%s`, so newer date alone is inadequate evidence of modern HAL architecture. Source licensing and complete vendor matching remain separate requirements. We do **not** reuse AOSPA/Lineage device trees as PE-Reborn's design base.

References:
- https://source.android.com/docs/core/audio/sound-trigger
- https://source.android.com/docs/core/audio/implement
- https://source.android.com/docs/core/audio/aidl-implement
- https://github.com/sonyxperiadev/vendor-qcom-opensource-audio-hal-st-hal-ar/tree/aosp/AUDIO.LA.10.0.r1
- https://github.com/sonyxperiadev/vendor-qcom-opensource-audio-hal-primary-hal-ar/tree/aosp/AUDIO.LA.10.0.r1
- https://github.com/PixelExperience-Reborn/hardware_interfaces/tree/port/a17-hardware-interfaces-pe-20261103

## Verified interface and loader distinction

### Historical C ST HAL (row 176)

`Android.mk` checks `BOARD_SUPPORTS_OPENSOURCE_STHAL`, excludes AudioReach when `TARGET_USES_QCOM_AUDIO_AR=true`, links old `sound_trigger_hw.c`, `st_hw_session_lsm.c`, `st_hw_session_gcs.c`, includes `KERNEL_OBJ/usr/techpack/audio/include`, uses `libgcs.so` for DSP graphs and installs a `sound_trigger.primary.*` shared library. It does **not** implement `android.hardware.soundtrigger3.ISoundTriggerHw/default` AIDL or a modern Binder service. Old GCS/LSM DSP interface and proprietary AHAL callback assumptions must not be transferred merely because both speak SoundTrigger framework concepts.

### Modern Qualcomm-derived AIDL and what it requires

`aosp/AUDIO.LA.10.0.r1` `Android.mk` builds **`libsoundtriggerhal.qti`**, compiles `src/soundtriggerhw/Service.cpp`, `SoundTriggerHw.cpp`, `SoundTriggerSession.cpp` plus PAL/NDK conversion and shared memory, links **`android.hardware.soundtrigger3-V1-ndk`**, `android.media.audio.common.types-V2-ndk` and `libar-pal`, and installs a VINTF fragment with precisely `android.hardware.soundtrigger3` AIDL **V1** `ISoundTriggerHw/default`.

`Service.cpp` **exports `createISoundTriggerFactory()`**: creates a `SoundTriggerHw` class instance and calls `AServiceManager_addService(..."/default")`. This library has **no own `init.rc`**; the product must configure a parent **`audiohalservice.qti`** to `dlopen` `libsoundtriggerhal.qti.so` and `dlsym` `createISoundTriggerFactory`. The modern primary service `hal/service/Service.cpp` does dynamic registration from `ConfigManager::parseInterfaces()` and can use a stub default if that configuration is missing. A module's source files and VINTF fragment do not prove it is installed or registered.

### SoundTrigger AIDL version and Audio 17 compatibility

Our exact selected PE AOSP17 `hardware/interfaces` has stable **SoundTrigger3 AIDL V1..V4**, with `latest_android_hardware_soundtrigger3` set to **V4**. The Qualcomm snapshot implements **V1**; the modern Android framework may support older versions but we must confirm this by comparing AIDL methods/versions, `SoundTriggerMiddleware` discovery, audio policy and VINTF/FCM, and performing VTS on the real selected device. **Do not claim it implements V4** or assume frozen V1 itself guarantees all Android17 device requirements.

AOSP17 core audio is separately AIDL-based. The Sony-hosted Qualcomm primary stack has Android17 Core **V3** and Effects **V4** source dependencies, but `configs/taro/audio_policy_configuration.xml` is still an older **XML v7.0** example. `taro` is a SoC family, not verified `mondrian` codec routing. We cannot copy this config to our independent product or claim a bootable AIDL Qualcomm HAL from the presence of that directory.

## SM8475 / taro compatibility and privacy gates

1. Confirm **stock Xiaomi vendor audio HAL** architecture/instances and Android interface versions from matched firmware or authorized device: `audio.core`, `audio.effect`, `soundtrigger3` or legacy soundtrigger HIDL, audio policy source, PAL/AGM/ACDB versions, exact model and DAI/codec/microphone arrays. Qualcomm target-board names `taro` or `sm8475` alone do not prove the ABI.
2. Resolve all AudioReach PAL, AGM, graphservices, audio-gpr, kernel audio-driver UAPI and proprietary ADSP firmware dependencies with ABI/ELF, Soong/Make tests. Determine OEM microphones, session IDs, graph IDs and soundmodel calibration; no magic assumptions or debug/permissive policy.
3. Enforce **one** system `android.hardware.soundtrigger3.ISoundTriggerHw/default` registration and matching device VINTF; no simultaneous `sound_trigger.primary.*` and AIDL registration, and no duplication between independent `libsoundtriggerhal.qti`/primary service processes.
4. Test Voice Call/Camcorder/VOIP/AudioRecord concurrency, recognition resource contention and wakeup, hotword capture buffers, crash/SSR recovery, ADSP suspend/power, thermal, screen-off privacy, microphone indicators and permission-enforcement. Android17 Audio Managed SCO may affect Bluetooth telephony routing. Device speaker/mics and always-on detection require real measurement.
5. Keep the PE-Reborn ROM independent. LF52406 LineageOS 24 device trees may only supply exceptional read-only hardware facts. No copying the complete Lineage device/product audio configuration or assuming Qualcomm AOSP Sony BSP is a Xiaomi product tree.

## GitHub/CI scope

An isolated historical audit branch contains a deterministic test of immutable old C/old PAL/new AIDL/modern primary/PAL/AGM/graphservice/config/PE AOSP17 interface sources. The manifest working branch contains a **source-only six-repo candidate** at `aosp17_pe_p2_qcom_audio_aidl_candidate.xml`. Exact project identities/SHAs, one Sony-hosted remote and 25 unchanged active stages are enforced, along with four adversarial tests against the old C checkout or premature promotion.

The CI verifies source pins, AIDL version/VINTF, dynamic service factory/loader and Qualcomm source graph; includes official `repo manifest` resolution and optionally targeted sync of only SoundTrigger/primary sources. No AOSP17 Soong/NDK binary build, full repo checkout, vendor proprietary BSP selection, device SELinux/VINTF or audio/hotword CTS/VTS has been done.

**Work is incomplete for functional device audio.** The newest generation is selected as a **reviewed source candidate**, not an enabled product component, until compatibility/boot/privacy gates pass.
