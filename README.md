
---

# GraderPro 📚✨  
> AI-powered handwritten exam sheets evaluation system

---

## 🔥 About GraderPro

GraderPro automates the **extraction**, **understanding**, **comparison**, and **scoring** of handwritten student answer sheets.  
Using OCR, LLMs, and semantic analysis, GraderPro saves time, ensures fairness, and delivers detailed feedback — instantly!

---

## 🚀 Features

- 🖨️ **PDF Uploads** (Handwritten sheets)
- 🔍 **OCR Text Extraction** (TrOCR + Gradio Client)
- 🧠 **Text Structuring** (Gemma 3:4B parsing)
- 🤝 **Student-Teacher Answer Matching**
- 📊 **AI-based Evaluation** (Keyword, Content, Grammar, Length)
- 🧮 **Weighted Marks Calculation**
- 🗃️ **MySQL Database Integration**
- 🔗 **FastAPI Server with REST APIs**
- 📑 **JSON Evaluation Reports**

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| FastAPI    | REST API Backend |
| MySQL      | Relational Database |
| pypdfium2  | PDF Page Rasterization |
| Gradio Client | OCR Model API Client |
| Ollama + Gemma 3:4B | Deep Language Evaluation |
| pandas     | Data Processing |
| uvicorn    | Server Deployment |

---

## ⚙️ How It Works

1. 📤 **Teacher uploads** solution sheets (PDF)
2. 📤 **Students upload** their answer sheets (PDF)
3. 🧠 **OCR + Parsing** turns scanned pages into structured digital text
4. 🔗 **Answer Matching** based on question numbers
5. 🧮 **Scoring** based on:
   - Keyword Matching
   - Content Relevance
   - Grammar Correctness
   - Word Count Compliance
6. 📝 **Report Generation** per question + full paper marks
7. 📦 **Results saved** in MySQL for future retrieval

   ## System Architecture

![GraderPro](GraderPro%201.3.png)

---

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|:------:|:--------:|:--------|
| `POST` | `/upload/teacherPdf` | Upload teacher PDF (auto digitize) |
| `POST` | `/upload/studentPdf` | Upload student PDF (auto digitize) |
| `GET`  | `/evaluateStudentSheet?student_id=...&teacher_id=...` | Evaluate student's sheet |
| `GET`  | `/getAllResult` | Get all evaluations |
| `GET`  | `/getResult/{student_id}` | Get a student's detailed report |

---

## 📦 Setup Instructions

1. **Clone the repo**

```bash
git clone https://github.com/prakashvk2003/GraderPro.git
cd GraderPro
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run MySQL locally**
- Create a database named `GraderPro_db`
- Update `db_manager.py` credentials if needed

4. **Start the server**

```bash
python app.py
```

Server runs at:  
`http://localhost:8000/docs` ➔ Swagger UI to test APIs 📜

---

## 🛣️ Future Roadmap

- [ ] Frontend dashboard (GraderPro Web)
- [ ] Plagiarism detection module
- [ ] Rubric-based customizable scoring
- [ ] Batch uploads for whole classes
- [ ] AI feedback on writing style

---

## 🤝 Contribution

Pull requests are welcome!  
Let's build a smarter educational future together.

---


## Contact

 - Vikash Rautela      - [Rautelavikash27@gmail.com](mailto:Rautelavikash27@gmail.com)
 - Prakash Vishwakarma - [prakashvk2003@gmail.com](mailto:prakashvk2003@gmail.com)
