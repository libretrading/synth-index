import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.title("Indice Sintetico (€) – dal 16 aprile 2025 a oggi")

# 1) Date: start sempre fisso al 2025‑04‑16, end a oggi
start = datetime(2024, 4, 16)
end   = datetime.today()
start_str = start.strftime('%Y-%m-%d')
end_str   = end.strftime('%Y-%m-%d')

# 2) Pesi raw e scala da 75→100
raw_weights = {
    'BRK-B': 7.5, 'EVO.ST': 5.6, 'UBER': 5.6,
    'GOOG': 3.75, 'KSPI': 3.75, 'NU': 3.75,
    'MELI': 3.75, 'SBSW': 1.86, 'ALB': 1.86
}
scale = 100/75
scaled_pct = {t: w*scale for t,w in raw_weights.items()}
cash_pct = 100 - sum(scaled_pct.values())

# 3) Frazioni iniziali
init_frac = {t: pct/100 for t,pct in scaled_pct.items()}
init_frac['CASH'] = cash_pct/100

# 4) Download prezzi Adjusted Close
fx = ['EURUSD=X','EURSEK=X']
tickers = list(raw_weights) + fx
data = yf.download(
    tickers,
    start=start_str,
    end=end_str,
    auto_adjust=False,
    progress=False
)['Adj Close']

# 5) Conversione in EUR
price_eur = pd.DataFrame(index=data.index)
for t in raw_weights:
    if t.endswith('.ST'):
        price_eur[t] = data[t] / data['EURSEK=X']
    else:
        price_eur[t] = data[t] / data['EURUSD=X']

# 6) Rendimenti ed indice
rets = price_eur.pct_change().fillna(0)
idx_ret = sum(init_frac[t]*rets[t] for t in raw_weights)  # cash = 0
idx_level = (1+idx_ret).cumprod() * 100

# 7) Pesi finali
start_prices = price_eur.loc[start_str]
end_prices   = price_eur.iloc[-1]
value_end = {t: init_frac[t] * (end_prices[t]/start_prices[t]) for t in raw_weights}
value_end['CASH'] = init_frac['CASH']
tot_end = sum(value_end.values())
end_frac = {t: v/tot_end for t,v in value_end.items()}

# 8) Plot e tabella
fig, (ax1, ax2) = plt.subplots(2,1, figsize=(10,8),
                                gridspec_kw={'height_ratios':[3,1]})
# grafico
ax1.plot(idx_level.index, idx_level.values)
ax1.set_title(f"Indice Sintetico (€) – da {start_str} a {end_str}")
ax1.set_xlabel("Data"); ax1.set_ylabel("Livello")
ax1.grid(linestyle='--', alpha=0.4)

# tabella
assets = list(raw_weights.keys()) + ['CASH']
init_w = [f"{scaled_pct[t]:.2f}%" for t in raw_weights] + [f"{cash_pct:.2f}%"]
end_w  = [f"{end_frac[t]*100:.2f}%" for t in raw_weights] + [f"{end_frac['CASH']*100:.2f}%"]
tbl_data = list(zip(assets, init_w, end_w))

ax2.axis('off')
tbl = ax2.table(
    cellText=tbl_data,
    colLabels=['Asset','Peso Iniziale','Peso Finale'],
    loc='center'
)
tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1,1.5)

st.pyplot(fig)
