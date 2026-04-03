from model_ci_loader import LAB_PATH, _read_excel_with_fallback

for mid in [1750,1860,2264]:
    name = f"Z_{mid}"
    try:
        df = _read_excel_with_fallback(LAB_PATH, name)
        ok = not df.empty
    except Exception as e:
        ok = False
    print(name, 'OK' if ok else 'MISSING')
