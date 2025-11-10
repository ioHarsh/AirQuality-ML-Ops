
---

## ⚡ How It Works
1. **Data Generation** → Creates new synthetic air quality readings daily  
2. **Pipeline Execution** → `pipeline.py` trains and evaluates model  
3. **Model Output** → Saves predictions to `/artifacts/predictions`  
4. **Dashboard** → Reads latest output, updates AQI charts automatically  
5. **Task Scheduler** → Runs `run_pipeline.ps1` daily to automate everything

---

## 🧰 Tech Stack
| Component | Tool |
|------------|------|
| Programming | Python |
| Libraries | pandas, numpy, scikit-learn, streamlit, altair |
| Automation | YAML + Task Scheduler |
| IDE | Visual Studio Code |

---

## 🧠 Setup & Run
```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/AirQuality-ML-Ops.git
cd AirQuality-ML-Ops

# 2. Create & activate virtual environment
python -m venv venv
venv\Scripts\activate   # for Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run pipeline manually
python pipeline.py

# 5. Launch Streamlit dashboard
python -m streamlit run src/dashboard.py
