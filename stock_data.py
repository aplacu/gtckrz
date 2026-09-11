# Daftar Saham Aktif BEI - Hasil Validasi
# Data ini sudah difilter untuk hanya menyertakan saham aktif
# Update: 2026-03-03 08:31:49
# Disinkronkan dengan idx_all_tickers.py

SECTOR_STOCKS = {
    "Financials (Keuangan)": [
        "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK", "ARTO.JK", 
        "BBTN.JK", "PNBN.JK", "BDMN.JK", "BFIN.JK", "BNGA.JK", "NISP.JK", 
        "MEGA.JK", "BTPS.JK", "BJBR.JK", "BJTM.JK", "TUGU.JK", "ADMF.JK", 
        "AMAR.JK", "AGRO.JK", "BANK.JK", "BBHI.JK", "BCIC.JK", "BBYB.JK", 
        "PNBS.JK", "MAYA.JK", "NOBU.JK", "BBKP.JK", "DNAR.JK", "BVIC.JK", 
        "BABP.JK", "BGTG.JK", "BKSW.JK", "BSIM.JK", "MCOR.JK", "BINA.JK", 
        "MASB.JK", "BACA.JK", "VICO.JK", "BEKS.JK", "BTPN.JK", "BNLI.JK", 
        "BNII.JK", "BBLD.JK", "CFIN.JK", "DEFI.JK", "GSMF.JK", "HDFA.JK", 
        "IMJS.JK", "TIFA.JK", "VRNA.JK", "WOMF.JK", "AHAP.JK", "AMAG.JK", 
        "ASBI.JK", "ASDM.JK", "ASGR.JK", "ASJT.JK", "ASRM.JK", "LPGI.JK",
        "MREI.JK", "MTWI.JK", "PANS.JK", "PNLF.JK", "TRIM.JK", "VINS.JK", 
        "YULE.JK", "AMIN.JK", "BAPA.JK", "BBYB.JK", "BCAP.JK", "BESS.JK", 
        "BISI.JK", "BVIC.JK", "COCO.JK", "DNAR.JK", "IBST.JK", "INPC.JK", 
        "ITIC.JK", "JSPT.JK", "KREN.JK", "LPPS.JK", "MREI.JK", "MTFN.JK", 
        "PADI.JK", "RELI.JK", "SDRA.JK", "SMDM.JK", "TARA.JK", "VICO.JK", 
        "YULE.JK"
    ],

    "Energy (Energi)": [
        "ADRO.JK", "PTBA.JK", "PGAS.JK", "AKRA.JK", "MEDC.JK", "ITMG.JK", 
        "HRUM.JK", "INDY.JK", "DOID.JK", "ELSA.JK", "BUMI.JK", "ENRG.JK", 
        "DEWA.JK", "TOBA.JK", "ADMR.JK", "MBSS.JK", "RAJA.JK", "AIMS.JK", 
        "WINE.JK", "SGER.JK", "CUAN.JK", "GEMS.JK", "BYAN.JK", "DSSA.JK", 
        "KKGI.JK", "MYOH.JK", "TEBE.JK", "BSSR.JK", "GTBO.JK", "FIRE.JK", 
        "CNKO.JK", "PKPK.JK", "IATA.JK", "LEAD.JK", "APEX.JK", "BIPI.JK", 
        "BULL.JK", "COAL.JK", "DWGL.JK", "GTSI.JK", "HUMI.JK", "INPS.JK", 
        "RIGS.JK", "SOCI.JK", "TAMU.JK", "WOWS.JK", "AADI.JK", "PTRO.JK", 
        "TCPI.JK", "RMKE.JK", "OKAS.JK", "APEX.JK", "MITI.JK", "PKPK.JK", 
        "BULL.JK", "CANI.JK", "OASA.JK", "SEMA.JK"
    ],

    "Basic Materials (Barang Baku)": [
        "TPIA.JK", "MDKA.JK", "INKP.JK", "TKIM.JK", "ANTM.JK", "INCO.JK", 
        "SMGR.JK", "INTP.JK", "BRPT.JK", "ESSA.JK", "MBMA.JK", "NCKL.JK", 
        "HRTA.JK", "ZINC.JK", "WOOD.JK", "MARK.JK", "BRMS.JK", "PSAB.JK", 
        "DKFT.JK", "NICL.JK", "TINS.JK", "AVIA.JK", "AMMN.JK", "LTLS.JK", 
        "ARNA.JK", "SMBR.JK", "KRAS.JK", "IFSH.JK", "AGII.JK", "MOLI.JK", 
        "OKAS.JK", "ALDO.JK", "ALKA.JK", "BAJA.JK", "BTON.JK", "CTBN.JK", 
        "GDST.JK", "INAI.JK", "ISSP.JK", "LION.JK", "NIKL.JK", "PICO.JK", 
        "TBMS.JK", "AMMN.JK", "BRPT.JK", "SUNI.JK", "BMHS.JK", "ESIP.JK", 
        "IPCC.JK", "KMTR.JK", "MICE.JK", "NELY.JK", "PSSI.JK", "RAJA.JK", 
        "SCCO.JK", "TAYS.JK", "URBN.JK"
    ],

    "Infrastructures (Infrastruktur)": [
        "TLKM.JK", "ISAT.JK", "EXCL.JK", "JSMR.JK", "PGEO.JK", "TBIG.JK", 
        "TOWR.JK", "ADHI.JK", "PTPP.JK", "CENT.JK", "POWR.JK", "KEEN.JK", 
        "LINK.JK", "MTEL.JK", "BALI.JK", "OASA.JK", "LCKM.JK", "GIAA.JK", 
        "CMPP.JK", "WEGE.JK", "ACST.JK", "BESS.JK", "BTEK.JK", "BUKK.JK", 
        "DGIK.JK", "IDPR.JK", "JKON.JK", "NRCA.JK", "PPRE.JK", "SSIA.JK", 
        "TOTL.JK", "CDIA.JK", "BREN.JK", "MORA.JK", "BUKK.JK", "CMNP.JK", 
        "DART.JK", "GOLD.JK", "KBLI.JK", "LUCK.JK", "PORT.JK", "PURA.JK", 
        "SKRN.JK", "TOWR.JK"
    ],

    "Consumer Non-Cyclical (Primer)": [
        "ICBP.JK", "INDF.JK", "UNVR.JK", "GGRM.JK", "HMSP.JK", "MYOR.JK", 
        "CPIN.JK", "AMRT.JK", "JPFA.JK", "CMRY.JK", "GOOD.JK", "CLEO.JK", 
        "ULTJ.JK", "ROTI.JK", "KINO.JK", "CPRO.JK", "AISA.JK", "TBLA.JK", 
        "LSIP.JK", "AALI.JK", "DSNG.JK", "TAPG.JK", "SSMS.JK", "SIMP.JK", 
        "MIDI.JK", "WIIM.JK", "ITIC.JK", "MAIN.JK", "FISH.JK", "KEJU.JK", 
        "CAMP.JK", "PCAR.JK", "ADES.JK", "KJEN.JK", "PADA.JK", "ADMG.JK", 
        "AKPI.JK", "ALDO.JK", "AMFG.JK", "APLI.JK", "ARGO.JK", "BATA.JK", 
        "BRNA.JK", "DLTA.JK", "DVLA.JK", "EKAD.JK", "ESTI.JK", "GDYR.JK", 
        "IKAI.JK", "INCI.JK", "INDR.JK", "JECC.JK", "KAEF.JK", "KBLM.JK", 
        "KDSI.JK", "KICI.JK", "KLBF.JK", "FISH.JK", "GZCO.JK", "HOKI.JK", 
        "IPTV.JK", "KEJU.JK", "MLBI.JK", "MPPA.JK", "PSDN.JK", "SKBM.JK"
    ],

    "Consumer Cyclical (Non-Primer)": [
        "MAPI.JK", "ACES.JK", "ERAA.JK", "SCMA.JK", "MSIN.JK", "AUTO.JK", 
        "MNCN.JK", "RALS.JK", "LPPF.JK", "MAPA.JK", "FILM.JK", "IMAS.JK", 
        "GJTL.JK", "MPMX.JK", "BOLA.JK", "MAPB.JK", "DRMA.JK", "ASLC.JK", 
        "TOOL.JK", "INDS.JK", "SMSM.JK", "BOLT.JK", "PBRX.JK", "BELL.JK", 
        "ZONE.JK", "SOCI.JK", "CSAP.JK", "WOOD.JK", "MDRN.JK", "VIVA.JK", 
        "MDIA.JK", "AKKU.JK", "AMIN.JK", "APII.JK", "ASRI.JK", "BATA.JK", 
        "BLUE.JK", "CARS.JK", "CINT.JK", "DNET.JK", "DYAN.JK", "ECII.JK", 
        "ELTY.JK", "ERAA.JK", "GEMA.JK", "HERO.JK", "FILM.JK", "AMMN.JK", 
        "BOLA.JK", "DNET.JK", "ERAA.JK", "GEMA.JK", "HERO.JK", "ICON.JK", 
        "INDS.JK", "JSPT.JK", "LPKR.JK", "MDRN.JK", "MPMX.JK", "PBRX.JK", 
        "RALS.JK", "SCMA.JK", "SMSM.JK", "TARA.JK", "VIVA.JK"
    ],

    "Technology (Teknologi)": [
        "GOTO.JK", "EMTK.JK", "BUKA.JK", "MTDL.JK", "WIRG.JK", "BELI.JK", 
        "MLPT.JK", "MCAS.JK", "DMMX.JK", "KIOS.JK", "NFCX.JK", "UVCR.JK", 
        "AWAN.JK", "WIFI.JK", "GLVA.JK", "LUCK.JK", "HDIT.JK", "DIVA.JK", 
        "ATIC.JK", "KREN.JK", "MMLP.JK", "NETV.JK", "PTSN.JK", "SPTO.JK", 
        "TFAS.JK", "ZYRX.JK", "KREN.JK", "MLPT.JK", "MTDL.JK", "PTSN.JK"
    ],

    "Healthcare (Kesehatan)": [
        "KLBF.JK", "MIKA.JK", "SILO.JK", "HEAL.JK", "KAEF.JK", "SIDO.JK", 
        "IRRA.JK", "PRDA.JK", "SAME.JK", "TSPC.JK", "MERK.JK", "SRAJ.JK", 
        "PRIM.JK", "BMHS.JK", "CARE.JK", "DGNS.JK", "PEHA.JK", "PYFA.JK", 
        "SOHO.JK", "OMRE.JK", "PEHA.JK", "SRAJ.JK"
    ],

    "Transportation & Logistics": [
        "GIAA.JK", "BIRD.JK", "SMDR.JK", "TMAS.JK", "ASSA.JK", "PSSI.JK", 
        "NELY.JK", "IPCC.JK", "TRJA.JK", "WEHA.JK", "BPTR.JK", "CARS.JK", 
        "LRNA.JK", "TRUK.JK", "TNCA.JK", "HAIS.JK", "PPGL.JK", "SAPX.JK", 
        "KRYA.JK", "AKSI.JK", "JAYA.JK", "KOCI.JK", "MIRA.JK", "SAFE.JK",
        "SDMU.JK", "WBSA.JK"
    ],

    "Properties & Real Estate": [
        "BSDE.JK", "PWON.JK", "CTRA.JK", "SMRA.JK", "ASRI.JK", "LPKR.JK", 
        "APLN.JK", "DMAS.JK", "PANI.JK", "MKPI.JK", "BEST.JK", "BKSL.JK", 
        "DILD.JK", "KIJA.JK", "JRPT.JK", "MDLN.JK", "LPCK.JK", "DUTI.JK", 
        "MTLA.JK", "RDTX.JK", "GPRA.JK", "GWSA.JK", "SSIA.JK", "CITY.JK", 
        "URBN.JK", "ROCK.JK", "ADCP.JK", "AMAN.JK", "BAPA.JK", "BIPP.JK", 
        "COCO.JK", "ELTY.JK", "EMDE.JK", "FMII.JK", "GMTD.JK", "LAND.JK", 
        "LPLI.JK", "MMLP.JK", "NIRO.JK", "POLI.JK", "RISE.JK", "TARA.JK"
    ],

    "Industrials (Perindustrian)": [
        "ASII.JK", "UNTR.JK", "HEXA.JK", "IMPC.JK", "BMTR.JK", "ABMM.JK", 
        "KOBX.JK", "DYAN.JK", "KBLI.JK", "VOKS.JK", "JECC.JK", "ARGO.JK", 
        "ALKA.JK", "LION.JK", "SCCO.JK", "IKBI.JK", "SPMA.JK", "AMIN.JK", 
        "INTD.JK", "AMFG.JK", "APLI.JK", "BATA.JK", "BRNA.JK", "BTEK.JK", 
        "DLTA.JK", "DVLA.JK", "EKAD.JK", "ESTI.JK", "GDYR.JK", "IKAI.JK", 
        "IMAS.JK", "INCI.JK", "INDR.JK", "KBLM.JK", "KDSI.JK", "KICI.JK", 
        "KBLI.JK", "VOKS.JK", "JECC.JK"
    ],
}

# Normalisasi daftar:
# 1) Hapus duplikasi di dalam sektor
# 2) Hapus duplikasi antar sektor (ticker masuk ke sektor pertama yang menemukannya)
# Tujuan: jumlah saham yang discan = jumlah ticker unik yang valid.
_seen_global = set()
for _sector, _tickers in list(SECTOR_STOCKS.items()):
    _seen_sector = set()
    _normalized = []
    for _t in _tickers:
        if _t in _seen_sector:
            continue
        _seen_sector.add(_t)
        if _t in _seen_global:
            continue
        _seen_global.add(_t)
        _normalized.append(_t)
    SECTOR_STOCKS[_sector] = _normalized

del _sector, _tickers, _seen_sector, _normalized, _t, _seen_global
