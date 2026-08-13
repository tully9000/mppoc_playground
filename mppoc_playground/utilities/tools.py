



def timestamp_output_dir():
    # ── Per-run output folder ────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = args.run_id or f"{args.label}_{timestamp}"
    out_dir = (args.output_root / run_id).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    driver_cfg.setdefault("general", {})["folder_output"] = str(out_dir)
    driver_cfg.setdefault("recorder", {}).update(
        {"flag": True, "overwrite_recorder": True}
    )
    driver_cfg["recorder"].setdefault("file", "cases.sql")


def make_manifest():
    # ── Log what was used (before running, so failures stay documented) ──
    manifest = {
        "run_id": run_id,
        "label": args.label,
        "timestamp": timestamp,
        "git_commit": _git_commit(case_dir),
        "case_dir": str(case_dir),
        "output_dir": str(out_dir),
        "n_timesteps": plant_cfg["plant"]["simulation"]["n_timesteps"],
        "overrides": overrides,
        "control_parameters": control_params,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))