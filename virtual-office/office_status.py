"""Read-only office view of the team registry and gateway heartbeat."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {} if default is None else default


def timestamp(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def process_exists(pid):
    try:
        if not isinstance(pid, int) or pid <= 0:
            return False
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


DEFINITIONS = {
    "pm": {
        "name": "PM Intan", "short_name": "PM Intan", "role": "Koordinasi & arahan",
        "group": "Dapur produksi", "initials": "PI", "room": "01",
        "description": "Menyusun brief, membagi tugas, dan memeriksa hasil sebelum dibawa ke pemilik.",
        "responsibilities": ["Perencanaan dan brief konten", "Koordinasi researcher dan talent", "Pemeriksaan paket untuk persetujuan"],
    },
    "researcher": {
        "name": "Researcher", "short_name": "Researcher", "role": "Riset & penulisan",
        "group": "Dapur produksi", "initials": "RS", "room": "02",
        "description": "Memeriksa sumber publik dan menyiapkan temuan, hook, serta draf caption untuk PM.",
        "responsibilities": ["Riset dan pemeriksaan sumber", "Brief tren dan kandidat sound", "Draf hook dan caption"],
    },
    "dinda": {
        "name": "Dinda Kemala", "short_name": "Dinda", "role": "Talent · Palembang",
        "group": "Studio talent", "initials": "DK", "room": "03",
        "description": "Talent daily vlog, lifestyle, dan kuliner Palembang. Pilot konten sudah melewati review dan ACC.",
        "responsibilities": ["Konten sesuai identitas Dinda", "Balasan DM dan komentar dalam sesi manual", "Pemeriksaan paket sebelum publikasi"],
    },
    "nara": {
        "name": "Nara Adelia", "short_name": "Nara", "role": "Talent · Medan",
        "group": "Studio talent", "initials": "NA", "room": "04",
        "description": "Talent beauty, GRWM, dan keseharian bekerja di Medan. Pengujian produksi masih menunggu.",
        "responsibilities": ["Konten beauty dan GRWM", "Gaya kantor dan keseharian Medan", "Menjaga konsistensi identitas Nara"],
    },
    "rania": {
        "name": "Rania Meutia", "short_name": "Rania", "role": "Talent · Aceh",
        "group": "Studio talent", "initials": "RM", "room": "05",
        "description": "Talent wisata alam, hidden gems, dan kuliner wisata Aceh dengan modest travel look.",
        "responsibilities": ["Wisata alam dan destinasi Aceh", "Kuliner di sekitar tempat wisata", "Menjaga konsistensi identitas Rania"],
    },
    "sales": {
        "name": "Agent Sales", "short_name": "Sales", "role": "Penjualan toko",
        "group": "Operasional", "initials": "SL", "room": "06",
        "description": "Menyiapkan konsultasi produk, draf penawaran dan pesanan, serta ringkasan prospek.",
        "responsibilities": ["Konsultasi dan rekomendasi produk", "Draf penawaran dan pesanan", "Penyerahan ke sales manusia"],
    },
    "default": {
        "name": "Hermes utama", "short_name": "Hermes utama", "role": "Gateway tim",
        "group": "Operasional", "initials": "HM", "room": "07",
        "description": "Penghubung profil tim Hermes. Status diambil dari heartbeat lokal, terpisah dari hasil uji tiap agen.",
        "responsibilities": ["Melayani profil tim", "Menampilkan status proses", "Menjaga jalur koordinasi"],
    },
}


def get_office_status(project_dir, hermes_home=None, now=None):
    project_dir = Path(project_dir)
    hermes_home = Path(hermes_home) if hermes_home else Path.home() / ".hermes"
    now = now or datetime.now(timezone.utc)
    project = read_json(project_dir / "config/project.json")
    config = read_json(project_dir / "config/hermes.json")
    sales = read_json(project_dir / "config/sales.json")
    gateway = read_json(hermes_home / "gateway_state.json")
    updated = timestamp(gateway.get("updated_at"))
    fresh = updated is not None and 0 <= (now - updated).total_seconds() <= 120
    alive = process_exists(gateway.get("pid"))
    running = fresh and alive and gateway.get("gateway_state") == "running"
    served = set(gateway.get("served_profiles") or []) if running else set()
    gateway_state = "running" if running else ("stale" if gateway and not fresh else "stopped")
    agents = []
    for key in ["pm", "researcher", "dinda", "nara", "rania", "sales", "default"]:
        profile = (config.get("profiles") or {}).get(key, {})
        if key != "default" and not profile:
            continue
        definition = dict(DEFINITIONS[key])
        profile_name = "default" if key == "default" else profile.get("name")
        paused = key == "sales" and not sales.get("whatsapp", {}).get("gateway_enabled", False)
        if paused:
            runtime, runtime_label = "paused", "Ditunda"
        elif profile_name in served:
            runtime, runtime_label = "available", "Gateway aktif" if key == "default" else "Siap internal"
        elif gateway_state == "stale":
            runtime, runtime_label = "unknown", "Status belum terbarui"
        else:
            runtime, runtime_label = "offline", "Gateway tidak melayani"
        model = profile.get("model") or config.get("model") or {}
        checks = []
        if key == "default":
            stage = "Status gateway"
            checks = [{"label": "Heartbeat", "value": "Terbarui" if fresh else "Belum terbarui"},
                      {"label": "Proses", "value": "Berjalan" if running else "Belum terkonfirmasi"}]
            limitation = "Gateway berjalan sebagai proses terpisah; pemulihan otomatis macOS belum terverifikasi."
        elif key == "sales":
            stage = "WhatsApp ditunda"
            checks = [{"label": "Setup agen", "value": "Selesai"}, {"label": "Uji model", "value": "Belum dijalankan"},
                      {"label": "Katalog toko", "value": "Belum diisi"}]
            limitation = "Koneksi dan balasan WhatsApp tetap ditunda. Harga serta stok harus berasal dari data toko yang disahkan."
        elif key in {"nara", "rania"}:
            stage = "Uji produksi menunggu"
            checks = [{"label": "Model", "value": "Lulus uji" if "passed" in profile.get("model_test_status", "") else "Belum diverifikasi"},
                      {"label": "Tugas lokal", "value": "Lulus uji" if "passed" in profile.get("coordination_test_status", "") else "Belum diverifikasi"},
                      {"label": "Browser & produksi", "value": "Belum diuji"}]
            limitation = "Akses browser dan akun Flow belum lulus uji produksi. Jadwal rutin belum aktif."
        elif key == "dinda":
            stage = "Pilot konten berhasil" if profile.get("generation_download_tested") else "Uji produksi menunggu"
            checks = [{"label": "Generate & download", "value": "Lulus uji" if profile.get("generation_download_tested") else "Belum diuji"},
                      {"label": "DM & komentar manual", "value": "Lulus uji" if "passed" in profile.get("engagement_test_status", "") else "Belum diverifikasi"},
                      {"label": "Adapter kirim baru", "value": "Belum diuji langsung"}]
            limitation = "Publikasi tetap memerlukan paket final, ACC yang sesuai, dan izin publikasi terpisah."
        elif key == "researcher":
            stage = "Brief publik lulus uji" if "passed" in profile.get("coordination_test_status", "") else "Uji riset menunggu"
            checks = [{"label": "Sumber publik", "value": "Lulus uji" if "passed" in profile.get("coordination_test_status", "") else "Belum diverifikasi"},
                      {"label": "Serah terima ke PM", "value": "Lulus uji" if "pm_readback" in profile.get("coordination_test_status", "") else "Belum diverifikasi"},
                      {"label": "Tren & sound TikTok", "value": "Perlu validasi lanjutan"}]
            limitation = "Brief riset historis bukan bukti bahwa agen sedang melakukan riset saat ini."
        else:
            passed = "passed" in (config.get("coordination") or {}).get("runtime_test", "")
            stage = "Koordinasi lulus uji" if passed else "Koordinasi disiapkan"
            checks = [{"label": "Pembagian tugas", "value": "Lulus uji" if passed else "Belum diverifikasi"},
                      {"label": "Pembacaan hasil", "value": "Lulus uji" if passed else "Belum diverifikasi"},
                      {"label": "Produksi rutin", "value": "Belum aktif"}]
            limitation = "Persetujuan konten tidak otomatis mengaktifkan publikasi, pembelian, atau generasi baru."
        definition.update(id=key, profile=profile_name, model=model.get("default", "Belum diatur"),
                          runtime=runtime, runtime_label=runtime_label, stage=stage,
                          checks=checks, limitation=limitation)
        agents.append(definition)

    accounts = read_json(project_dir / "config/flow_accounts.json").get("accounts", [])
    verified = [a for a in accounts if a.get("balance_verified") and a.get("verified_balance") is not None]
    flow = {"balance": None, "verified_at": None, "account": None, "verified_accounts": len(verified),
            "unverified_accounts": len(accounts) - len(verified)}
    # Account balances are separate; never invent a pooled balance.
    if verified:
        account = verified[0]
        flow.update(balance=account["verified_balance"], verified_at=account.get("balance_verified_at"),
                    account=account.get("chrome_profile_label") or account.get("id"))
    pilot = read_json(project_dir / "config/pilot.json")
    return {
        "checked_at": now.isoformat(),
        "agents": agents,
        "runtime": {"state": gateway_state, "updated_at": gateway.get("updated_at"),
                    "active_agents": gateway.get("active_agents") if running else None,
                    "served_profiles": sorted(served)},
        "permissions": {key: bool(project.get(key)) for key in
                        ["generation_enabled", "publication_enabled", "scheduler_enabled", "telegram_enabled"]},
        "flow": flow,
        "pilot": {"spent": pilot.get("actual_credits"), "cap": pilot.get("flow_total_credit_cap")},
    }
