"""
Skrip untuk sinkronisasi stock_data.py dengan idx_all_tickers.py
Menggunakan yfinance untuk mendapatkan informasi sektor
"""
import yfinance as yf
from core.idx_all_tickers import IDX_TICKERS
import json

# Mapping sektor IDX ke kategori kita - lebih lengkap
SECTOR_MAPPING = {
    # Financials
    'Financials': 'Financials (Keuangan)',
    'Financial Services': 'Financials (Keuangan)',
    'Banks': 'Financials (Keuangan)',
    'Capital Markets': 'Financials (Keuangan)',
    'Insurance': 'Financials (Keuangan)',
    'Diversified Financial Services': 'Financials (Keuangan)',
    
    # Energy
    'Energy': 'Energy (Energi)',
    'Oil & Gas': 'Energy (Energi)',
    'Oil & Gas Drilling': 'Energy (Energi)',
    'Oil & Gas Exploration & Production': 'Energy (Energi)',
    'Oil & Gas Refining & Marketing': 'Energy (Energi)',
    'Coal': 'Energy (Energi)',
    
    # Basic Materials
    'Basic Materials': 'Basic Materials (Barang Baku)',
    'Materials': 'Basic Materials (Barang Baku)',
    'Chemicals': 'Basic Materials (Barang Baku)',
    'Construction Materials': 'Basic Materials (Barang Baku)',
    'Metals & Mining': 'Basic Materials (Barang Baku)',
    'Paper & Forest Products': 'Basic Materials (Barang Baku)',
    'Aluminum': 'Basic Materials (Barang Baku)',
    'Gold': 'Basic Materials (Barang Baku)',
    'Steel': 'Basic Materials (Barang Baku)',
    
    # Industrials
    'Industrials': 'Industrials (Perindustrian)',
    'Capital Goods': 'Industrials (Perindustrian)',
    'Commercial Services & Supplies': 'Industrials (Perindustrian)',
    'Transportation Infrastructure': 'Industrials (Perindustrian)',
    'Machinery': 'Industrials (Perindustrian)',
    'Building Products': 'Industrials (Perindustrian)',
    'Construction & Engineering': 'Industrials (Perindustrian)',
    'Aerospace & Defense': 'Industrials (Perindustrian)',
    'Electrical Equipment': 'Industrials (Perindustrian)',
    
    # Consumer Discretionary
    'Consumer Discretionary': 'Consumer Cyclical (Non-Primer)',
    'Consumer Cyclical': 'Consumer Cyclical (Non-Primer)',
    'Automobiles': 'Consumer Cyclical (Non-Primer)',
    'Retail': 'Consumer Cyclical (Non-Primer)',
    'Media': 'Consumer Cyclical (Non-Primer)',
    'Hotels & Motels': 'Consumer Cyclical (Non-Primer)',
    'Leisure': 'Consumer Cyclical (Non-Primer)',
    'Textiles & Apparel': 'Consumer Cyclical (Non-Primer)',
    'Household Durables': 'Consumer Cyclical (Non-Primer)',
    
    # Consumer Staples
    'Consumer Staples': 'Consumer Non-Cyclical (Primer)',
    'Consumer Non-Cyclical': 'Consumer Non-Cyclical (Primer)',
    'Food Products': 'Consumer Non-Cyclical (Primer)',
    'Beverages': 'Consumer Non-Cyclical (Primer)',
    'Tobacco': 'Consumer Non-Cyclical (Primer)',
    'Household Products': 'Consumer Non-Cyclical (Primer)',
    'Personal Products': 'Consumer Non-Cyclical (Primer)',
    'Food & Staples Retailing': 'Consumer Non-Cyclical (Primer)',
    
    # Healthcare
    'Health Care': 'Healthcare (Kesehatan)',
    'Healthcare': 'Healthcare (Kesehatan)',
    'Healthcare Equipment & Supplies': 'Healthcare (Kesehatan)',
    'Healthcare Providers & Services': 'Healthcare (Kesehatan)',
    'Pharmaceuticals': 'Healthcare (Kesehatan)',
    'Biotechnology': 'Healthcare (Kesehatan)',
    'Life Sciences Tools & Services': 'Healthcare (Kesehatan)',
    
    # Technology
    'Information Technology': 'Technology (Teknologi)',
    'Technology': 'Technology (Teknologi)',
    'Software': 'Technology (Teknologi)',
    'IT Services': 'Technology (Teknologi)',
    'Semiconductors': 'Technology (Teknologi)',
    'Hardware': 'Technology (Teknologi)',
    'Electronic Equipment': 'Technology (Teknologi)',
    
    # Communication Services
    'Communication Services': 'Technology (Teknologi)',
    'Telecommunication Services': 'Technology (Teknologi)',
    'Wireless Telecommunication Services': 'Technology (Teknologi)',
    'Diversified Telecommunication Services': 'Technology (Teknologi)',
    
    # Real Estate
    'Real Estate': 'Properties & Real Estate',
    'Real Estate Management & Development': 'Properties & Real Estate)',
    'REITs': 'Properties & Real Estate)',
    
    # Utilities
    'Utilities': 'Infrastructures (Infrastruktur)',
    'Electric Utilities': 'Infrastructures (Infrastruktur)',
    'Multi-Utilities': 'Infrastructures (Infrastruktur)',
    'Water Utilities': 'Infrastructures (Infrastruktur)',
    'Gas Utilities': 'Infrastructures (Infrastruktur)',
    
    # Transportation
    'Transportation': 'Transportation & Logistics',
    'Transportation': 'Transportation & Logistics',
    'Airlines': 'Transportation & Logistics',
    'Marine': 'Transportation & Logistics',
    'Road & Rail': 'Transportation & Logistics',
    'Logistics': 'Transportation & Logistics',
}

def get_sector_from_yfinance(ticker):
    """Mendapatkan sektor dari yfinance"""
    try:
        stock = yf.Ticker(f"{ticker}.JK")
        info = stock.info
        sector = info.get('sector', None)
        industry = info.get('industry', None)
        
        # Mapping ke kategori kita
        if sector in SECTOR_MAPPING:
            return SECTOR_MAPPING[sector]
        
        # Cek industry untuk Transportation
        if industry and 'transport' in industry.lower():
            return 'Transportation & Logistics'
            
        return None
    except Exception as e:
        return None

def main():
    print(f"Menganalisis {len(IDX_TICKERS)} ticker...")
    
    # Inisialisasi dictionary sektor
    sector_stocks = {
        "Financials (Keuangan)": [],
        "Energy (Energi)": [],
        "Basic Materials (Barang Baku)": [],
        "Infrastructures (Infrastruktur)": [],
        "Consumer Non-Cyclical (Primer)": [],
        "Consumer Cyclical (Non-Primer)": [],
        "Technology (Teknologi)": [],
        "Healthcare (Kesehatan)": [],
        "Transportation & Logistics": [],
        "Properties & Real Estate": [],
        "Industrials (Perindustrian)": [],
    }
    
    unknown_tickers = []
    
    # Proses setiap ticker
    for i, ticker in enumerate(IDX_TICKERS):
        if (i + 1) % 50 == 0:
            print(f"Memproses {i + 1}/{len(IDX_TICKERS)}...")
        
        sector = get_sector_from_yfinance(ticker)
        
        if sector and sector in sector_stocks:
            sector_stocks[sector].append(f"{ticker}.JK")
        else:
            unknown_tickers.append(ticker)
    
    # Cetak hasil
    print("\n=== Hasil Sinkronisasi ===")
    for sector, stocks in sector_stocks.items():
        print(f"{sector}: {len(stocks)} saham")
    
    print(f"\nTicker tanpa informasi sektor: {len(unknown_tickers)}")
    print(f"Ticker: {unknown_tickers[:20]}...")  # Tampilkan 20 pertama
    
    # Generate output
    print("\n=== Output untuk stock_data.py ===")
    for sector, stocks in sector_stocks.items():
        if stocks:
            print(f'\n    "{sector}": [')
            # Print dalam kolom
            for i in range(0, len(stocks), 6):
                row = stocks[i:i+6]
                print(f'        "{'", "'.join(row)}",')
            print('    ],')

if __name__ == "__main__":
    main()
