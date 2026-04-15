# 📈 Stock Dashboard — Value Investing

Dashboard financiero para analizar acciones del S&P 500, NASDAQ, IBEX 35 y principales índices europeos usando métricas de **value investing** (PER, P/B, PEG, EV/EBITDA, ROE…) más un **Score de Valor 0–100** calculado automáticamente.

---

## 🖥️ 1. Ejecutar en local

### Requisitos previos
- **Python 3.9+** — [python.org](https://www.python.org/downloads/)
- Conexión a internet (para obtener datos de Yahoo Finance)

### macOS / Linux

```bash
# 1. Entra en la carpeta del proyecto
cd stock-dashboard

# 2. Dale permisos de ejecución al script (solo la primera vez)
chmod +x start.sh

# 3. Lanza el dashboard
./start.sh
```

El script instala las dependencias automáticamente y abre el navegador en `http://localhost:5000`.

### Windows

Haz doble clic en `start.bat` o ejecuta desde CMD:

```bat
cd stock-dashboard
start.bat
```

El script instala las dependencias y abre el navegador automáticamente.

### Instalación manual (alternativa)

```bash
pip install flask flask-cors yfinance pandas gunicorn
python app.py
# Abre http://localhost:5000 en tu navegador
```

---

## ☁️ 2. Desplegar en Railway (gratis, un clic)

1. Sube el proyecto a un repositorio de **GitHub** (público o privado).
2. Ve a [railway.app](https://railway.app) y crea una cuenta gratuita.
3. Haz clic en **"New Project" → "Deploy from GitHub repo"**.
4. Selecciona tu repositorio. Railway detectará el `Procfile` automáticamente.
5. En la sección **Settings → Networking**, genera un dominio público.
6. ¡Listo! En 2–3 minutos tendrás el dashboard en una URL pública como `https://stock-dashboard-xxx.up.railway.app`.

> Railway inyecta automáticamente la variable de entorno `PORT`. El servidor Flask la lee para escuchar en el puerto correcto.

### Desplegar en Render (alternativa gratuita)

1. Ve a [render.com](https://render.com) → **New Web Service**.
2. Conecta tu repositorio de GitHub.
3. Configura:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Haz clic en **Create Web Service**.

---

## ➕ 3. Añadir o eliminar tickers

### Desde el dashboard (recomendado)
1. Haz clic en el botón **⚙️ Gestionar tickers** en la parte superior.
2. Verás todos los tickers activos como chips.
3. Haz clic en **×** para eliminar uno.
4. Escribe el símbolo en el campo "Añadir ticker" y pulsa **+ Añadir**.
5. Haz clic en **🔄 Refrescar** para cargar los nuevos datos.

> Los tickers se guardan en `localStorage` del navegador, por lo que persisten entre sesiones.

### Cambiar la lista por defecto (en el código)
Edita la constante `TICKERS` en `data.py`:

```python
TICKERS = [
    "AAPL", "MSFT", "GOOGL",  # S&P 500 / NASDAQ
    "ITX.MC", "SAN.MC",        # IBEX 35 (sufijo .MC)
    "MC.PA", "SAP.DE",         # Europa (.PA = París, .DE = Frankfurt)
    "NESN.SW",                 # Suiza
    # ... añade los que quieras
]
```

**Sufijos de Yahoo Finance por mercado:**
| Sufijo | Bolsa |
|--------|-------|
| *(sin sufijo)* | NASDAQ / NYSE (EE.UU.) |
| `.MC` | Bolsa de Madrid (IBEX 35) |
| `.PA` | Euronext París |
| `.DE` | XETRA Frankfurt |
| `.SW` | SIX Suiza |
| `.L`  | London Stock Exchange |
| `.AS` | Euronext Ámsterdam |
| `.MI` | Borsa Italiana |
| `.HK` | Hong Kong |

---

## 🔔 4. Configurar alertas con Make.com (Zapier)

El dashboard puede enviarte una notificación automática cuando una acción cambia su señal a **COMPRAR**.

### Paso a paso con Make.com

1. Crea una cuenta gratuita en [make.com](https://www.make.com).
2. Crea un nuevo **Escenario**.
3. Añade el módulo **Webhooks → Custom Webhook** como trigger.
4. Haz clic en **Add** → Make te genera una URL como `https://hook.eu1.make.com/abc123xyz`.
5. Conecta a continuación los módulos que quieras: Email, Telegram, Slack, Google Sheets, etc.
6. **Copia la URL del webhook**.
7. Abre el dashboard → **⚙️ Gestionar tickers** → pega la URL en el campo **"Webhook URL (alertas)"**.
8. La URL se guarda automáticamente en `localStorage`.

Cada vez que se refresca el dashboard y una acción **pasa de NEUTRAL/VENDER → COMPRAR**, recibirás una notificación con:

```json
{
  "ticker":  "AAPL",
  "name":    "Apple Inc.",
  "signal":  "COMPRAR",
  "score":   72.5,
  "price":   185.40,
  "change":  1.23,
  "market":  "US",
  "ts":      "2025-01-15T10:30:00Z"
}
```

> **Nota:** Las alertas solo funcionan en sesiones de navegador activas, no en el servidor.  
> Para alertas programadas en el servidor, configura un cron job que llame a `/api/refresh` periódicamente.

---

## 📊 Cómo se calcula el Score de Valor

El score (0–100) pondera 8 métricas fundamentales:

| Métrica | Peso | Ideal |
|---------|------|-------|
| PER | 20% | < 15 |
| PEG | 15% | < 1 |
| EV/EBITDA | 15% | < 8 |
| P/Book | 10% | < 1.5 |
| Deuda/Equity | 10% | < 50% |
| ROE | 10% | > 20% |
| Margen Operativo | 10% | > 20% |
| RSI-14 | 10% | 20–35 (sobrevendido) |

Si una métrica no está disponible, su peso se redistribuye proporcionalmente entre las demás.

**Señal final:**
- 🟢 **COMPRAR** → Score ≥ 65
- 🟡 **NEUTRAL** → Score 35–64
- 🔴 **VENDER** → Score < 35

---

## 🗂️ Estructura del proyecto

```
stock-dashboard/
├── app.py           # Servidor Flask (endpoints REST)
├── data.py          # Lógica: yfinance, RSI, scoring, caché
├── dashboard.html   # Frontend (Tailwind CSS + Chart.js)
├── requirements.txt # Dependencias Python
├── start.sh         # Arranque Mac/Linux
├── start.bat        # Arranque Windows
├── Procfile         # Para Railway/Render
└── README.md        # Este fichero
```

---

## ⚡ API REST

| Endpoint | Descripción |
|----------|-------------|
| `GET /` | Sirve el dashboard HTML |
| `GET /api/stocks?tickers=AAPL,MSFT` | Lista de acciones con score y señal |
| `GET /api/stock/AAPL` | Detalle completo con historial y desglose del score |
| `GET /api/refresh` | Invalida la caché (fuerza recarga de datos) |
| `GET /api/tickers` | Lista de tickers por defecto |

La caché tiene un TTL de **4 horas** para no saturar la API de Yahoo Finance.

---

## 🛟 Solución de problemas

**"Error al cargar datos"** en el navegador  
→ Asegúrate de que el servidor Flask está corriendo (`python app.py`).

**Datos vacíos o N/D para algunas acciones**  
→ Yahoo Finance no siempre tiene todos los datos. Es normal para small caps o acciones de mercados menos líquidos.

**Ticker no encontrado**  
→ Verifica el símbolo exacto en [finance.yahoo.com](https://finance.yahoo.com) buscando la empresa.

**Puerto 5000 en uso (macOS Monterey+)**  
→ El puerto 5000 puede estar ocupado por AirPlay. Lanza con: `PORT=5001 python app.py`
