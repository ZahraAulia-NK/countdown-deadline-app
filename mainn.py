"""
COUNTDOWN DEADLINE TUGAS KULIAH
MVC + GUI 
"""

import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime
from functools import wraps
import json, os

# ══════════════════════════════════════════
# 6. NAMEDTUPLE
# ══════════════════════════════════════════

SisaWaktu = namedtuple("SisaWaktu", ["hari", "jam", "menit", "detik", "terlambat"])

# ══════════════════════════════════════════
# 5. DECORATOR
# ══════════════════════════════════════════

def validasi_nama(func):
    @wraps(func)
    def wrapper(self, nama, *args, **kwargs):
        if not nama or not nama.strip():
            raise ValueError("Nama tugas tidak boleh kosong!")
        return func(self, nama.strip(), *args, **kwargs)
    return wrapper

# ══════════════════════════════════════════
# 4. ABSTRACT BASE CLASS
# ══════════════════════════════════════════

class TugasBase(ABC):
    _jumlah_tugas = 0  # 5. Class Attribute

    def __init__(self, id_, nama, matkul, deadline):
        TugasBase._jumlah_tugas += 1
        self.id       = id_
        self.nama     = nama
        self.matkul   = matkul
        self.deadline = deadline
        self.selesai  = False

    @classmethod
    def total_tugas(cls):
        return cls._jumlah_tugas

    @abstractmethod
    def jenis(self) -> str: pass

    @abstractmethod
    def ikon(self) -> str: pass

    def sisa_waktu(self) -> SisaWaktu:
        delta = self.deadline - datetime.now()
        terlambat = delta.total_seconds() < 0
        if terlambat: delta = -delta
        total = int(delta.total_seconds())
        return SisaWaktu(
            hari=delta.days,
            jam=(total % 86400) // 3600,
            menit=(total % 3600) // 60,
            detik=total % 60,
            terlambat=terlambat
        )

    def countdown(self) -> str:
        if self.selesai: return "Selesai ✓"
        s = self.sisa_waktu()
        tanda = "-" if s.terlambat else ""
        return f"{tanda}{s.hari}h {s.jam:02d}:{s.menit:02d}:{s.detik:02d}"

    def status(self) -> str:
        if self.selesai: return "Selesai"
        s = self.sisa_waktu()
        total_s = s.hari*86400 + s.jam*3600 + s.menit*60 + s.detik
        if s.terlambat:       return "Terlambat"
        if total_s < 3600:    return "< 1 Jam!"
        if total_s < 86400:   return "< 1 Hari"
        return "On Track"

    def to_dict(self):
        return {"id": self.id, "nama": self.nama, "matkul": self.matkul,
                "deadline": self.deadline.isoformat(), "selesai": self.selesai,
                "tipe": self.__class__.__name__}

# ══════════════════════════════════════════
# 1 & 2. CLASS + INHERITANCE
# 3. POLYMORPHISM (jenis & ikon berbeda)
# ══════════════════════════════════════════

class TugasIndividu(TugasBase):
    def __init__(self, id_, nama, matkul, deadline, bobot=10):
        super().__init__(id_, nama, matkul, deadline)
        self.bobot = bobot

    def jenis(self): return f"Individu · {self.bobot}%"
    def ikon(self):  return "👤"

    def to_dict(self):
        d = super().to_dict(); d["bobot"] = self.bobot; return d

class TugasKelompok(TugasBase):
    def __init__(self, id_, nama, matkul, deadline, anggota=3):
        super().__init__(id_, nama, matkul, deadline)
        self.anggota = anggota

    def jenis(self): return f"Kelompok · {self.anggota} org"
    def ikon(self):  return "👥"

    def to_dict(self):
        d = super().to_dict(); d["anggota"] = self.anggota; return d

class TugasUjian(TugasBase):
    def __init__(self, id_, nama, matkul, deadline, ruang="A101"):
        super().__init__(id_, nama, matkul, deadline)
        self.ruang = ruang

    def jenis(self): return f"Ujian · {self.ruang}"
    def ikon(self):  return "📝"

    def to_dict(self):
        d = super().to_dict(); d["ruang"] = self.ruang; return d

# ══════════════════════════════════════════
# 7. DESIGN PATTERN — Factory
# ══════════════════════════════════════════

class TugasFactory:
    @staticmethod
    def buat(tipe, id_, nama, matkul, deadline, **kw):
        if tipe == "TugasKelompok":
            return TugasKelompok(id_, nama, matkul, deadline, kw.get("anggota", 3))
        if tipe == "TugasUjian":
            return TugasUjian(id_, nama, matkul, deadline, kw.get("ruang", "A101"))
        return TugasIndividu(id_, nama, matkul, deadline, kw.get("bobot", 10))

    @staticmethod
    def dari_dict(d):
        tipe  = d.get("tipe", "TugasIndividu")
        tugas = TugasFactory.buat(
            tipe, d["id"], d["nama"], d["matkul"],
            datetime.fromisoformat(d["deadline"]),
            bobot=d.get("bobot", 10),
            anggota=d.get("anggota", 3),
            ruang=d.get("ruang", "A101"),
        )
        tugas.selesai = d.get("selesai", False)
        return tugas

# ══════════════════════════════════════════
# 7. DESIGN PATTERN — Observer
# ══════════════════════════════════════════

class Observer(ABC):
    @abstractmethod
    def update(self, event, data=None): pass

class Observable:
    def __init__(self):
        self._obs = []
    def subscribe(self, o): self._obs.append(o)
    def notify(self, event, data=None):
        for o in self._obs: o.update(event, data)

# ══════════════════════════════════════════
# MVC — MODEL (Singleton)
# ══════════════════════════════════════════

FILE = os.path.join(os.path.expanduser("~"), ".tugas_kuliah.json")

class _SingleMeta(type):
    _inst = {}
    def __call__(cls, *a, **kw):
        if cls not in cls._inst:
            cls._inst[cls] = super().__call__(*a, **kw)
        return cls._inst[cls]

class ModelTugas(Observable, metaclass=_SingleMeta):
    def __init__(self):
        super().__init__()
        self._tugas = []
        self._next  = 1
        self._muat()

    @validasi_nama
    def tambah(self, nama, matkul, deadline, tipe="TugasIndividu", **kw):
        t = TugasFactory.buat(tipe, self._next, nama, matkul, deadline, **kw)
        self._tugas.append(t); self._next += 1
        self._simpan(); self.notify("tambah", t)

    def hapus(self, id_):
        t = self._cari(id_)
        if t: self._tugas.remove(t); self._simpan(); self.notify("hapus", id_)

    def toggle(self, id_):
        t = self._cari(id_)
        if t: t.selesai = not t.selesai; self._simpan(); self.notify("update", t)

    def daftar(self, status="Semua", tipe="Semua"):
        res = self._tugas[:]
        if status == "Aktif":   res = [t for t in res if not t.selesai]
        if status == "Selesai": res = [t for t in res if t.selesai]
        if tipe != "Semua":     res = [t for t in res if t.__class__.__name__ == tipe]
        return sorted(res, key=lambda t: (t.selesai, t.deadline))

    def _cari(self, id_): return next((t for t in self._tugas if t.id == id_), None)
    def cari(self, id_):  return self._cari(id_)

    def _simpan(self):
        with open(FILE, "w") as f:
            json.dump({"next": self._next,
                       "data": [t.to_dict() for t in self._tugas]}, f, indent=2)

    def _muat(self):
        if not os.path.exists(FILE): return
        try:
            with open(FILE) as f: raw = json.load(f)
            self._next  = raw.get("next", 1)
            self._tugas = [TugasFactory.dari_dict(d) for d in raw.get("data", [])]
        except: pass

# ══════════════════════════════════════════
# MVC — VIEW
# ══════════════════════════════════════════

C = {
    "bg":  "#0f0f1a", "card": "#1a1a2e", "sel": "#16213e",
    "bdr": "#0f3460",  "txt": "#e0e0e0", "dim": "#7f8c8d",
    "acc": "#e94560",  "grn": "#2ecc71", "ylw": "#f39c12",
    "pur": "#9b59b6",  "blu": "#3498db", "tl":  "#1abc9c",
}

TIPE_C = {
    "TugasIndividu":  C["blu"],
    "TugasKelompok":  C["pur"],
    "TugasUjian":     C["acc"],
}

STATUS_C = {
    "On Track": C["grn"], "< 1 Hari": C["ylw"],
    "< 1 Jam!": C["acc"], "Terlambat": C["acc"],
    "Selesai":  C["dim"],
}

class DialogTambah(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Tambah Tugas")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.result = None
        self._build()
        self.grab_set(); self.transient(parent)

    def _lbl(self, f, t):
        tk.Label(f, text=t, bg=C["bg"], fg=C["dim"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(6,0))

    def _ent(self, f, v):
        e = tk.Entry(f, textvariable=v, bg=C["card"], fg=C["txt"],
                     insertbackground=C["acc"], relief="flat",
                     font=("Segoe UI", 10), width=28)
        e.pack(fill="x", ipady=4)
        return e

    def _build(self):
        f = tk.Frame(self, bg=C["bg"], padx=22, pady=18); f.pack()

        self.v_nama   = tk.StringVar()
        self.v_matkul = tk.StringVar()
        self.v_tgl    = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.v_jam    = tk.StringVar(value="23:59")
        self.v_tipe   = tk.StringVar(value="TugasIndividu")
        self.v_extra  = tk.StringVar(value="10")

        self._lbl(f, "Nama Tugas")
        self._ent(f, self.v_nama)
        self._lbl(f, "Mata Kuliah")
        self._ent(f, self.v_matkul)
        self._lbl(f, "Tanggal Deadline  (YYYY-MM-DD)")
        self._ent(f, self.v_tgl)
        self._lbl(f, "Jam  (HH:MM)")
        self._ent(f, self.v_jam)

        self._lbl(f, "Jenis Tugas")
        rf = tk.Frame(f, bg=C["bg"]); rf.pack(fill="x", pady=(4,0))
        for val, lbl in [("TugasIndividu","Individu"),
                         ("TugasKelompok","Kelompok"),
                         ("TugasUjian",   "Ujian")]:
            tk.Radiobutton(rf, text=lbl, variable=self.v_tipe, value=val,
                           bg=C["bg"], fg=C["txt"], selectcolor=C["card"],
                           activebackground=C["bg"], font=("Segoe UI",9),
                           command=self._ubah_extra
                           ).pack(side="left", padx=6)

        self.v_extra_lbl = tk.StringVar(value="Bobot nilai (%):")
        tk.Label(f, textvariable=self.v_extra_lbl, bg=C["bg"], fg=C["dim"],
                 font=("Segoe UI",9)).pack(anchor="w", pady=(8,0))
        self.extra_frame = tk.Frame(f, bg=C["bg"]); self.extra_frame.pack(fill="x")
        self._build_extra()

        bf = tk.Frame(f, bg=C["bg"]); bf.pack(fill="x", pady=(14,0))
        tk.Button(bf, text="Batal", bg=C["card"], fg=C["dim"],
                  relief="flat", font=("Segoe UI",9),
                  command=self.destroy, padx=10, pady=5).pack(side="left")
        tk.Button(bf, text="Simpan", bg=C["acc"], fg="white",
                  relief="flat", font=("Segoe UI",9,"bold"),
                  command=self._submit, padx=10, pady=5).pack(side="right")

    def _build_extra(self):
        for w in self.extra_frame.winfo_children(): w.destroy()
        tipe = self.v_tipe.get()
        if tipe == "TugasIndividu":
            self.v_extra_lbl.set("Bobot nilai (%):")
            self.v_extra.set("10")
            for val in ("5","10","15","20","30"):
                tk.Radiobutton(self.extra_frame, text=val+"%",
                               variable=self.v_extra, value=val,
                               bg=C["bg"], fg=C["txt"], selectcolor=C["card"],
                               activebackground=C["bg"],
                               font=("Segoe UI",9)).pack(side="left",padx=4)
        elif tipe == "TugasKelompok":
            self.v_extra_lbl.set("Jumlah anggota:")
            self.v_extra.set("3")
            for val in ("2","3","4","5"):
                tk.Radiobutton(self.extra_frame, text=val+" org",
                               variable=self.v_extra, value=val,
                               bg=C["bg"], fg=C["txt"], selectcolor=C["card"],
                               activebackground=C["bg"],
                               font=("Segoe UI",9)).pack(side="left",padx=4)
        else:
            self.v_extra_lbl.set("Ruang ujian:")
            self.v_extra.set("A101")
            e = tk.Entry(self.extra_frame, textvariable=self.v_extra,
                         bg=C["card"], fg=C["txt"], insertbackground=C["acc"],
                         relief="flat", font=("Segoe UI",10), width=10)
            e.pack(anchor="w", ipady=4)

    def _ubah_extra(self): self._build_extra()

    def _submit(self):
        nama   = self.v_nama.get().strip()
        matkul = self.v_matkul.get().strip()
        if not nama or not matkul:
            messagebox.showerror("Error","Nama & matkul wajib diisi!",parent=self)
            return
        try:
            dl = datetime.strptime(
                f"{self.v_tgl.get()} {self.v_jam.get()}", "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error","Format tanggal/jam salah!",parent=self)
            return
        tipe  = self.v_tipe.get()
        extra = self.v_extra.get()
        kw = {}
        if tipe == "TugasIndividu":  kw["bobot"]   = int(extra)
        elif tipe == "TugasKelompok": kw["anggota"] = int(extra)
        else:                         kw["ruang"]   = extra
        self.result = (nama, matkul, dl, tipe, kw)
        self.destroy()


class ViewUtama(tk.Tk, Observer):
    def __init__(self):
        super().__init__()
        self.title("Deadline Tugas Kuliah")
        self.configure(bg=C["bg"])
        self.minsize(720, 500)
        self._ctrl  = None
        self._sel   = None
        self._f_status = tk.StringVar(value="Semua")
        self._f_tipe   = tk.StringVar(value="Semua")
        self._build()

    def set_controller(self, ctrl): self._ctrl = ctrl

    def update(self, event, data=None): self.refresh()

    # ── Build UI ───────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=C["acc"], pady=10); hdr.pack(fill="x")
        tk.Label(hdr, text="📅  DEADLINE TUGAS KULIAH",
                 bg=C["acc"], fg="white",
                 font=("Segoe UI", 14, "bold")).pack()

        # Filter
        fb = tk.Frame(self, bg=C["card"], padx=10, pady=5); fb.pack(fill="x")
        tk.Label(fb, text="Status:", bg=C["card"], fg=C["dim"],
                 font=("Segoe UI",8)).pack(side="left")
        for s in ("Semua","Aktif","Selesai"):
            tk.Radiobutton(fb, text=s, variable=self._f_status, value=s,
                           bg=C["card"], fg=C["txt"], selectcolor=C["sel"],
                           activebackground=C["card"], font=("Segoe UI",8),
                           command=self.refresh).pack(side="left",padx=3)
        tk.Label(fb, text="  |  Jenis:", bg=C["card"], fg=C["dim"],
                 font=("Segoe UI",8)).pack(side="left")
        for t,l in [("Semua","Semua"),("TugasIndividu","Individu"),
                    ("TugasKelompok","Kelompok"),("TugasUjian","Ujian")]:
            tk.Radiobutton(fb, text=l, variable=self._f_tipe, value=t,
                           bg=C["card"], fg=C["txt"], selectcolor=C["sel"],
                           activebackground=C["card"], font=("Segoe UI",8),
                           command=self.refresh).pack(side="left",padx=3)

        # Body
        body = tk.Frame(self, bg=C["bg"]); body.pack(fill="both",expand=True,padx=8,pady=6)

        # Daftar tugas
        lf = tk.Frame(body, bg=C["bg"]); lf.pack(side="left",fill="both",expand=True)
        self._cvs = tk.Canvas(lf, bg=C["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(lf, orient="vertical", command=self._cvs.yview)
        self._cvs.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); self._cvs.pack(side="left",fill="both",expand=True)
        self._lf = tk.Frame(self._cvs, bg=C["bg"])
        self._cw = self._cvs.create_window((0,0), window=self._lf, anchor="nw")
        self._lf.bind("<Configure>",
            lambda e: self._cvs.configure(scrollregion=self._cvs.bbox("all")))
        self._cvs.bind("<Configure>",
            lambda e: self._cvs.itemconfig(self._cw, width=e.width))

        # Panel detail
        dp = tk.Frame(body, bg=C["card"], width=210, padx=10, pady=10)
        dp.pack(side="right",fill="y",padx=(6,0)); dp.pack_propagate(False)
        self._dp = dp
        self._build_detail()

        # Footer
        ft = tk.Frame(self, bg=C["sel"], padx=10, pady=5); ft.pack(fill="x")
        self._clk = tk.Label(ft, text="", bg=C["sel"], fg=C["dim"],
                             font=("Segoe UI",8)); self._clk.pack(side="left")
        tk.Button(ft, text="+ Tambah Tugas", bg=C["acc"], fg="white",
                  font=("Segoe UI",9,"bold"), relief="flat",
                  padx=12, pady=4, command=self._on_add).pack(side="right")

        self._tick()

    def _build_detail(self):
        d = self._dp
        tk.Label(d, text="DETAIL TUGAS", bg=C["card"], fg=C["acc"],
                 font=("Segoe UI",9,"bold")).pack(anchor="w")
        tk.Frame(d, height=1, bg=C["bdr"]).pack(fill="x", pady=3)

        self._dn   = tk.Label(d, text="—", bg=C["card"], fg=C["txt"],
                              font=("Segoe UI",10,"bold"),
                              wraplength=185, justify="left"); self._dn.pack(anchor="w")
        self._dm   = self._drow()
        self._dtp  = self._drow()
        self._ddl  = self._drow()
        self._dex  = self._drow()
        self._dcd  = self._drow()
        self._dst  = self._drow()

        tk.Frame(d, height=6, bg=C["card"]).pack()
        self._b_done = tk.Button(d, text="Tandai Selesai", bg=C["grn"],
                                 fg=C["bg"], font=("Segoe UI",8,"bold"),
                                 relief="flat", padx=6, pady=4,
                                 command=self._on_toggle, state="disabled")
        self._b_done.pack(fill="x", pady=2)
        self._b_del  = tk.Button(d, text="Hapus", bg=C["acc"],
                                 fg="white", font=("Segoe UI",8,"bold"),
                                 relief="flat", padx=6, pady=4,
                                 command=self._on_del, state="disabled")
        self._b_del.pack(fill="x", pady=2)

        tk.Frame(d, height=6, bg=C["card"]).pack()
        tk.Label(d, text="STATISTIK", bg=C["card"], fg=C["tl"],
                 font=("Segoe UI",8,"bold")).pack(anchor="w")
        tk.Frame(d, height=1, bg=C["bdr"]).pack(fill="x", pady=2)
        self._stat = tk.Label(d, text="", bg=C["card"], fg=C["dim"],
                              font=("Segoe UI",8), justify="left")
        self._stat.pack(anchor="w")

    def _drow(self):
        l = tk.Label(self._dp, text="", bg=C["card"], fg=C["dim"],
                     font=("Segoe UI",8), wraplength=185, justify="left")
        l.pack(anchor="w", pady=1); return l

    # ── Render ─────────────────────────────
    def refresh(self):
        if not self._ctrl: return
        tugas = self._ctrl.daftar(self._f_status.get(), self._f_tipe.get())
        for w in self._lf.winfo_children(): w.destroy()
        if not tugas:
            tk.Label(self._lf, text="Tidak ada tugas 🎉",
                     bg=C["bg"], fg=C["dim"],
                     font=("Segoe UI",11), pady=30).pack()
        else:
            for t in tugas: self._kartu(t)
        self._refresh_detail()
        self._refresh_stat()

    def _kartu(self, t):
        is_sel = t.id == self._sel
        bg  = C["sel"] if is_sel else C["card"]
        bdr = C["acc"] if is_sel else C["card"]
        st  = t.status()
        sc  = STATUS_C.get(st, C["dim"])
        tc  = TIPE_C.get(t.__class__.__name__, C["dim"])

        frm = tk.Frame(self._lf, bg=bdr, padx=2, pady=2, cursor="hand2")
        frm.pack(fill="x", pady=2, padx=2)
        inn = tk.Frame(frm, bg=bg, padx=10, pady=7)
        inn.pack(fill="both", expand=True)

        tk.Label(inn, text=t.ikon(), bg=bg,
                 font=("Segoe UI",15)).grid(row=0,column=0,rowspan=2,padx=(0,8))
        fg = C["dim"] if t.selesai else C["txt"]
        tk.Label(inn, text=t.nama, bg=bg, fg=fg,
                 font=("Segoe UI",9,"bold"), anchor="w"
                 ).grid(row=0,column=1,sticky="ew")
        tk.Label(inn, text=t.matkul, bg=bg, fg=C["dim"],
                 font=("Segoe UI",8), anchor="w"
                 ).grid(row=1,column=1,sticky="ew")

        ri = tk.Frame(inn, bg=bg); ri.grid(row=0,column=2,rowspan=2,padx=(8,0))
        tk.Label(ri, text=t.countdown(), bg=bg, fg=C["ylw"],
                 font=("Segoe UI",8,"bold")).pack(anchor="e")
        tk.Label(ri, text=st, bg=bg, fg=sc,
                 font=("Segoe UI",7)).pack(anchor="e")
        tk.Label(ri, text=t.jenis(), bg=bg, fg=tc,
                 font=("Segoe UI",7)).pack(anchor="e")
        inn.columnconfigure(1, weight=1)

        for w in (frm,inn)+tuple(inn.winfo_children())+tuple(ri.winfo_children()):
            w.bind("<Button-1>", lambda e, id_=t.id: self._on_sel(id_))

    def _refresh_detail(self):
        if not self._ctrl or not self._sel:
            self._dn.config(text="Pilih tugas")
            for l in (self._dm,self._dtp,self._ddl,self._dex,self._dcd,self._dst):
                l.config(text="")
            self._b_done.config(state="disabled")
            self._b_del.config(state="disabled"); return

        t = self._ctrl.cari(self._sel)
        if not t: return
        st = t.status()
        self._dn.config(text=t.nama)
        self._dm.config(text=f"Matkul : {t.matkul}")
        self._dtp.config(text=f"Jenis  : {t.__class__.__name__}",
                         fg=TIPE_C.get(t.__class__.__name__, C["dim"]))
        self._ddl.config(text=f"Deadline: {t.deadline.strftime('%d %b %Y %H:%M')}")
        self._dex.config(text=f"Info   : {t.jenis()}")
        self._dcd.config(text=f"Sisa   : {t.countdown()}", fg=C["ylw"])
        self._dst.config(text=f"Status : {st}",
                         fg=STATUS_C.get(st, C["dim"]))
        self._b_done.config(
            text="Batal Selesai" if t.selesai else "Tandai Selesai",
            state="normal")
        self._b_del.config(state="normal")

    def _refresh_stat(self):
        if not self._ctrl: return
        semua = self._ctrl.daftar()
        total   = len(semua)
        selesai = sum(1 for t in semua if t.selesai)
        aktif   = total - selesai
        telat   = sum(1 for t in semua if not t.selesai and t.status()=="Terlambat")
        ind = sum(1 for t in semua if isinstance(t, TugasIndividu))
        klp = sum(1 for t in semua if isinstance(t, TugasKelompok))
        ujn = sum(1 for t in semua if isinstance(t, TugasUjian))
        self._stat.config(text=(
            f"Total   : {total}\n"
            f"Aktif   : {aktif}\n"
            f"Selesai : {selesai}\n"
            f"Terlambat: {telat}\n"
            f"─────────────\n"
            f"Individu: {ind}\n"
            f"Kelompok: {klp}\n"
            f"Ujian   : {ujn}"
        ))

    def _tick(self):
        self._clk.config(
            text=datetime.now().strftime("  %A, %d %b %Y   %H:%M:%S"))
        if self._sel and self._ctrl:
            t = self._ctrl.cari(self._sel)
            if t: self._dcd.config(text=f"Sisa   : {t.countdown()}")
        self.after(1000, self._tick)

    # ── Events ─────────────────────────────
    def _on_add(self):
        if self._ctrl: self._ctrl.handle_tambah(self)

    def _on_sel(self, id_):
        self._sel = id_; self._refresh_detail()

    def _on_toggle(self):
        if self._ctrl and self._sel:
            self._ctrl.handle_toggle(self._sel); self.refresh()

    def _on_del(self):
        if self._ctrl and self._sel:
            self._ctrl.handle_hapus(self, self._sel)

# ══════════════════════════════════════════
# MVC — CONTROLLER
# ══════════════════════════════════════════

class Controller:
    def __init__(self, model: ModelTugas, view: ViewUtama):
        self._m = model; self._v = view
        model.subscribe(view); view.set_controller(self)

    def daftar(self, status="Semua", tipe="Semua"):
        return self._m.daftar(status, tipe)

    def cari(self, id_): return self._m.cari(id_)

    def handle_tambah(self, parent):
        dlg = DialogTambah(parent)
        parent.wait_window(dlg)
        if dlg.result:
            nama, matkul, dl, tipe, kw = dlg.result
            try:
                self._m.tambah(nama, matkul, dl, tipe, **kw)
                self._v.refresh()
            except ValueError as e:
                messagebox.showerror("Validasi", str(e))

    def handle_toggle(self, id_):
        self._m.toggle(id_); self._v.refresh()

    def handle_hapus(self, parent, id_):
        t = self._m.cari(id_)
        if t and messagebox.askyesno("Hapus", f"Hapus '{t.nama}'?", parent=parent):
            self._m.hapus(id_)
            self._v._sel = None
            self._v.refresh()

# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

def main():
    style_root = tk.Tk()
    s = ttk.Style(style_root)
    s.theme_use("clam")
    s.configure("Vertical.TScrollbar",
                background=C["sel"], troughcolor=C["bg"],
                bordercolor=C["bg"], arrowcolor=C["dim"])
    style_root.destroy()

    model = ModelTugas()
    view  = ViewUtama()
    ctrl  = Controller(model, view)
    view.refresh()
    view.mainloop()

if __name__ == "__main__":
    main()