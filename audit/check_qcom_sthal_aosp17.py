#!/usr/bin/env python3
"""PE-Reborn row176: immutable old/modern Qualcomm-derived STHAL source gate.

SOURCE ONLY: no Qualcomm license/CodeLinaro authenticity proof, no Soong
build, device firmware/DSP, VINTF/SELinux runtime, hotword mic or CTS/VTS.
Input order: old ST, old AR ST, newer ST, newer primary, PAL, AGM,
             graphservices, AudioReach conf, PE AOSP17 interfaces, manifest.
"""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

OLD_SHA = "68d8705deab99367a1c4022470feb7a4bf8cc785"
OLD_TREE = "1f74e1622de15d71d8999e6969932a1f0bce2f4a"
OLD_AR_SHA = "420362bced12aa266fbf73be76ee440b8341829f"
OLD_AR_TREE = "4e0987fea0b25cc46803456cd8e39c616d7602df"
ST_SHA = "1dcb1275256b3f43b78d342d623870324a831720"
ST_TREE = "d47390edeaf35ee6b50d15b88e9f5537f372174e"
PRIMARY_SHA = "b071e74ead44a7aecee69969003b902632cd4ab3"
PRIMARY_TREE = "c78551f4c27dab685e396cd8996c1458b724787d"
PAL_SHA = "44e6ad74fd34c390b053bbe19811502c132f007e"
PAL_TREE = "a1ec1aec66c66d7672fde7f3349bdef852a5d962"
AGM_SHA = "7ad4167f2241beefd2a48b9e87453c3a80c5811b"
AGM_TREE = "6c4eaa800ab4d1f2d584b51ae4e020eb68408c90"
GRAPH_SHA = "d38796b5d74ff727a5fbd9f10ecbc7f5c0335ff5"
GRAPH_TREE = "40286aaa0fbdfad8538496de1096d6b68b6e60a2"
CONF_SHA = "5e90f9e4d6bb790fca0a092d57fdee8572d5b990"
CONF_TREE = "76314d215f91c4125bc09ea48f6085eee02f3b1e"
IFACE_SHA = "735e364cbdd00b0d6e4dc33ea0866dbb6d971a11"
IFACE_TREE = "adad11a145a3ecd709642f720a53f5a923fce754"
NEW_PATHS = {
    "vendor/qcom/opensource/audio-hal/st-hal-ar": (
        "vendor-qcom-opensource-audio-hal-st-hal-ar", ST_SHA, ST_TREE),
    "vendor/qcom/opensource/audio-hal/primary-hal-ar": (
        "vendor-qcom-opensource-audio-hal-primary-hal-ar",
        PRIMARY_SHA, PRIMARY_TREE),
    "vendor/qcom/opensource/pal": (
        "vendor-qcom-opensource-arpal-lx", PAL_SHA, PAL_TREE),
    "vendor/qcom/opensource/agm": (
        "vendor-qcom-opensource-agm", AGM_SHA, AGM_TREE),
    "vendor/qcom/opensource/audioreach-graphservices": (
        "vendor-qcom-opensource-audioreach-graphservices",
        GRAPH_SHA, GRAPH_TREE),
    "vendor/qcom/opensource/audioreach-conf": (
        "vendor-qcom-opensource-audioreach-conf",
        CONF_SHA, CONF_TREE),
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True,
        stderr=subprocess.PIPE).strip()


def pin(root, ref, sha, tree, label):
    commit = git(root, "rev-parse", f"{ref}^{{commit}}")
    require(commit == sha, f"{label}: unexpected commit {commit}")
    tree_id = git(root, "rev-parse", f"{commit}^{{tree}}")
    require(tree_id == tree, f"{label}: unexpected tree {tree_id}")
    return commit


def show(root, rev, path):
    return git(root, "show", f"{rev}:{path}")


def blobs(root, rev):
    return git(root, "ls-tree", "-r", "--name-only", rev).splitlines()


def archived_legacy(root):
    old = pin(root, "refs/remotes/origin/seventeen",
              OLD_SHA, OLD_TREE, "2023 Qualcomm old LSM/GCS STHAL")
    src = blobs(root, old)
    make = show(root, old, "Android.mk")
    hw = show(root, old, "sound_trigger_hw.c")
    gcs = show(root, old, "st_hw_session_gcs.c")
    lsm = show(root, old, "st_hw_session_lsm.c")
    require(len(src) == 43,
            f"old Qualcomm legacy STHAL source file count drift: {len(src)}")
    for token in ("BOARD_SUPPORTS_OPENSOURCE_STHAL",
                  "ifneq ($(TARGET_USES_QCOM_AUDIO_AR),true)",
                  "LOCAL_MODULE := sound_trigger.primary.$(TARGET_BOARD_PLATFORM)",
                  "st_hw_session_lsm.c", "st_hw_session_gcs.c",
                  "LOCAL_C_INCLUDES += $(TARGET_OUT_HEADERS)/mm-audio/graphite-client",
                  "KERNEL_OBJ/usr/techpack/audio/include"):
        require(token in make,
                "legacy STHAL LSM/GCS/target platform graph drift: " + token)
    for token in ("<hardware/sound_trigger.h>", "sound_trigger_hw"):
        require(token in hw,
                "legacy C SoundTrigger HAL API drift: " + token)
    require('GCS_LIB "libgcs.so"' in gcs
            and "st_hw_session_gcs.h" in gcs
            and "st_hw_session_lsm.h" in lsm,
            "legacy DSP GCS/LSM backends changed")
    print("PASS: exact old 43-file C STHAL, GCS/LSM and kernel UAPI pinned")
    print("PASS: old C STHAL intentionally disabled for AUDIO_AR product")
    print("DECISION: no old sound_trigger.primary.* module in Android17 product")


def archived_audioreach(root):
    ref = pin(root, "refs/remotes/origin/seventeen",
              OLD_AR_SHA, OLD_AR_TREE, "2024 old PAL soundtrigger")
    require(len(blobs(root, ref)) == 10,
            "2024 old AudioReach STHAL file set changed")
    make = show(root, ref, "Android.mk")
    for token in (
        "TARGET_USES_QCOM_AUDIO_AR),true",
        "BOARD_SUPPORTS_OPENSOURCE_STHAL",
        "TARGET_USES_QCOM_MM_AUDIO",
        "LOCAL_MODULE               := sound_trigger.primary.$(TARGET_BOARD_PLATFORM)",
        "LOCAL_SHARED_LIBRARIES",
        "libar-pal",
    ):
        require(token in make, f"2024 PAL STHAL build changed: {token}")
    require("sound_trigger_hw_device" in show(
        root, ref, "SoundTriggerDevice.cpp"),
        "2024 PAL STHAL no longer uses legacy soundtrigger HW device")
    print("PASS: 2024 PAL-backed ST remains a legacy sound_trigger.primary.* HAL")


def official_interface(root):
    ref = pin(root, "refs/remotes/origin/port/a17-hardware-interfaces-pe-20261103",
              IFACE_SHA, IFACE_TREE, "selected PE AOSP17 hardware interfaces")
    bp = show(root, ref, "soundtrigger/aidl/Android.bp")
    aidl = show(root, ref,
                "soundtrigger/aidl/android/hardware/soundtrigger3/ISoundTriggerHw.aidl")
    require('name: "android.hardware.soundtrigger3"' in bp
            and 'stability: "vintf"' in bp and "frozen: true" in bp,
            "AOSP17 SoundTrigger3 frozen AIDL owner changed")
    for ver in ("1", "2", "3", "4"):
        require(f'version: "{ver}"' in bp
                and f"soundtrigger/aidl/aidl_api/android.hardware.soundtrigger3/{ver}/.hash"
                in blobs(root, ref),
                "AOSP17 SoundTrigger3 frozen version changed: " + ver)
    require('latest_android_hardware_soundtrigger3 = "android.hardware.soundtrigger3-V4"'
            in bp,
            "AOSP17 latest SoundTrigger3 interface version changed")
    require("interface ISoundTriggerHw" in aidl
            and "startRecognition(" in aidl
            and "registerGlobalCallback(" in aidl,
            "AOSP17 soundtrigger3 HAL API contract drift")
    print("PASS: selected PE AOSP17 hardware/interfaces owns frozen soundtrigger3 V1..V4")
    print("WARN: newer Qualcomm V1 HAL must prove runtime compat with AOSP17 V4")


def newest_qualcomm(st, primary, pal, agm, graph, conf):
    ref = pin(st, "refs/remotes/origin/aosp/AUDIO.LA.10.0.r1",
              ST_SHA, ST_TREE, "Sony-hosted Qualcomm AudioReach AIDL ST")
    make = show(st, ref, "Android.mk")
    service = show(st, ref, "src/soundtriggerhw/Service.cpp")
    implementation = show(st, ref, "src/soundtriggerhw/SoundTriggerHw.cpp")
    vintf = ET.fromstring(show(st, ref, "configs/soundtrigger.qti.xml"))
    require(len(blobs(st, ref)) == 19,
            "new Qualcomm-derived STHAL 19-file source footprint changed")
    for token in (
        "LOCAL_MODULE               := libsoundtriggerhal.qti",
        "LOCAL_VINTF_FRAGMENTS      := configs/soundtrigger.qti.xml",
        '"android.hardware.soundtrigger3-V1-ndk"',
        "android.hardware.soundtrigger3-V1-ndk",
        "libar-pal",
        "src/soundtriggerhw/Service.cpp",
    ):
        require(token in make,
                f"modern Qualcomm ST AIDL module/source link changed: {token}")
    require("createISoundTriggerFactory()" in service
            and "AServiceManager_addService(" in service
            and 'SoundTriggerHw::descriptor + "/default"' in service,
            "modern Qualcomm SoundTrigger3 AIDL Binder registration changed")
    require("namespace aidl::android::hardware::soundtrigger3"
            in implementation
            and "pal_set_param(" in implementation,
            "modern Qualcomm PAL-backed SoundTrigger3 implementation changed")
    hal = vintf.findall("hal")
    require(len(hal) == 1 and hal[0].get("format") == "aidl"
            and hal[0].findtext("name") == "android.hardware.soundtrigger3"
            and hal[0].findtext("version") == "1"
            and hal[0].findtext("fqname") == "ISoundTriggerHw/default",
            "modern Qualcomm STHAL VINTF must be AIDL V1, NOT V4")
    print("PASS: Qualcomm-derived AUDIO.LA.10.0.r1 STHAL is real AIDL V1")
    print("PASS: PAL-backed factory registration ISoundTriggerHw/default")
    print("WARN: STHAL is libsoundtriggerhal.qti factory, not init service alone")

    primary_ref = pin(primary, "refs/remotes/origin/aosp/AUDIO.LA.10.0.r1",
                      PRIMARY_SHA, PRIMARY_TREE, "Android17 Qualcomm primary HAL")
    top = show(primary, primary_ref, "Android.mk")
    service_bp = show(primary, primary_ref, "hal/service/Android.bp")
    service_cpp = show(primary, primary_ref, "hal/service/Service.cpp")
    policy = show(primary, primary_ref,
                  "configs/taro/audio_policy_configuration.xml")
    require("android.hardware.audio.core-V3-ndk" in top
            and "android.hardware.audio.effect-V4-ndk" in top
            and "PLATFORM_VERSION" in top,
            "new Qualcomm primary HAL Android17 core/effects version changed")
    require('name: "audiohalservice.qti"' in service_bp
            and 'init_rc: ["audiohalservice_qti.rc"]' in service_bp,
            "new primary HAL service implementation changed")
    for marker in ("dlopen(libraryName.c_str()", "dlsym(handle,",
                   "parseInterfaces()", "registerServices"):
        require(marker in service_cpp,
                "new primary HAL dynamic factory integration changed: " + marker)
    require('audioPolicyConfiguration version="7.0"' in policy,
            "taro source policy XML changed; re-evaluate hardware limitations")
    print("PASS: new primary source has Android17 Core V3/Effects V4")
    print("WARN: upstream taro audio policy is legacy XML v7.0; device ABI unproven")
    print("WARN: service must be configured to dlopen the STHAL AIDL factory")

    # A source-only 6-project preview does not assert all closed-source
    # audio DSP firmware, codecs, model licenses or vendor dependencies.
    companions = (
        (pal, PAL_SHA, PAL_TREE, "PAL", "Android.bp"),
        (agm, AGM_SHA, AGM_TREE, "AGM", "Android.mk"),
        (graph, GRAPH_SHA, GRAPH_TREE, "graphservices", "Android.mk"),
        (conf, CONF_SHA, CONF_TREE, "AudioReach config", "qcom/Android.bp"),
    )
    for root, commit, tree, label, buildfile in companions:
        revision = pin(root, "refs/remotes/origin/aosp/AUDIO.LA.10.0.r1",
                       commit, tree, "new Qualcomm " + label)
        require(buildfile in blobs(root, revision),
                f"new Qualcomm {label} build file disappeared: {buildfile}")
        require(len(blobs(root, revision)) > 20,
                f"new Qualcomm {label} source inventory suspiciously small")
        print(f"PASS: modern Qualcomm-derived {label} exact branch/commit/tree pinned")
    print("OPEN: DSP graph & firmware, PAL/AGM ABI, Audio Core version, taro routing")


def manifest(root):
    root = Path(root)
    d = ET.parse(root / "default.xml").getroot()
    require(len(d) == 1 and d[0].tag == "include"
            and d[0].get("name") == "aosp17_pe_p2_kernel_configs.xml",
            "default P2 source-only entrypoint was promoted unreviewed")
    b = ET.parse(root / "aosp17_pe_bootstrap.xml").getroot()
    owner = {p.get("path"): p.get("name") for p in b.findall("project")}
    require(owner.get("hardware/interfaces") == "platform/hardware/interfaces"
            and owner.get("frameworks/av") == "platform/frameworks/av",
            "AOSP17 interface/framework source base changed")
    candidate = ET.parse(
        root / "aosp17_pe_p2_qcom_audio_aidl_candidate.xml").getroot()
    nodes = list(candidate)
    require(len(nodes) == 8
            and [n.tag for n in nodes] ==
                ["include", "remote"] + ["project"] * 6
            and nodes[0].attrib ==
                {"name": "aosp17_pe_p2_kernel_configs.xml"}
            and nodes[1].attrib == {
                "name": "sony-qcom-audio-review",
                "fetch": "https://github.com/sonyxperiadev",
            }, "modern Qualcomm source preview structure/remote changed")
    require([x.get("path") for x in nodes[2:]] == list(NEW_PATHS),
            "Qualcomm audio candidate missing a required six-way source")
    for p in nodes[2:]:
        name, sha, _tree = NEW_PATHS[p.get("path")]
        require(p.attrib == {
            "path": p.get("path"), "name": name,
            "remote": "sony-qcom-audio-review",
            "revision": sha,
            "upstream": "refs/heads/aosp/AUDIO.LA.10.0.r1",
            "groups": "device",
        }, "Qualcomm source candidate moved remote/branch or immutable SHA")
    validator = (root / "tools/validate_aosp17_base_profiles.py").read_text()
    tests = (root / "tools/test_aosp17_manifest_entrypoint.py").read_text()
    require('if "vendor/qcom/opensource/audio-hal/st-hal" in projects:' in validator
            and '"vendor_qcom_opensource_audio-hal_st-hal"' in validator,
            "legacy Qualcomm old C STHAL manifest guard missing")
    for method in (
        "test_old_qualcomm_legacy_sthal_not_enabled_in_android17",
        "test_qualcomm_modern_six_repo_candidate_sha_is_immutable",
        "test_qualcomm_modern_candidate_requires_complete_source_set",
        "test_qualcomm_modern_candidate_cannot_replace_safe_default",
    ):
        require(f"def {method}(" in tests,
                "missing Qualcomm STHAL source graph test: " + method)
    subprocess.run(
        [sys.executable, str(root / "tools/validate_aosp17_base_profiles.py")],
        cwd=root, check=True)
    print("PASS: 25 selected AOSP17 manifest stages and 6 nondefault AIDL sources")
    print("PASS: no old STHAL checkout or change of AOSP17 frozen SoundTrigger AIDL")


def main():
    require(len(sys.argv) == 11,
            "Usage: oldST oldAR newST primary PAL AGM graph conf interfaces manifest")
    roots = [Path(x).resolve() for x in sys.argv[1:]]
    require(all(p.is_dir() for p in roots), "one or more Git source checkouts missing")
    archived_legacy(roots[0])
    archived_audioreach(roots[1])
    newest_qualcomm(*roots[2:8])
    official_interface(roots[8])
    manifest(roots[9])
    print("PASS: row176 new Qualcomm-derived AudioReach AIDL source reviewed")
    print("NOT TESTED: Android17 Soong/AIDL binary ABI, system audio service,")
    print("ADSP/ACDB, hotword/microphone privacy, device VINTF, CTS/VTS, mondrian")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError, ET.ParseError,
            subprocess.CalledProcessError) as e:
        print("FAIL:", e, file=sys.stderr)
        sys.exit(1)
