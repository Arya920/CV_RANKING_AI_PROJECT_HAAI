from litellm import completion

prompt = (
    """
    You are a hiring assistant. Given a resume summary and a job description summary, rate how well the resume fits the job on a scale of 1 to 10 and provide a brief explanation.
    Resume:
    "Experience": [
      {
        "Position": "SENIORCONSULTANT-DATASCIENCE",
        "Company": "NeosoftTechnologies",
        "Location": "Pune,India",
        "Start_Date": "2020-12-01",
        "End_Date": null
      },
      {
        "Position": "DATASCIENTIST",
        "Company": "NihilentLtd.",
        "Location": "Pune,India",
        "Start_Date": "2019-11-01",
        "End_Date": "2020-12-01"
      },
      {
        "Position": "DATASCIENTIST",
        "Company": "Infosys",
        "Location": "Pune,India",
        "Start_Date": "2017-12-01",
        "End_Date": "2019-06-01"
      },
      {
        "Position": "SOFTWAREENGINEER-WEBDEVELOPERINTERN",
        "Company": "EventbeepEntertainmentLLP",
        "Location": "Pune,India",
        "Start_Date": "2017-06-01",
        "End_Date": "2017-12-01"
      }
    ],
    "Technical Skills": [
      "Python",
      "SQL",
      "MachineLearning",
      "DeepLearning",
      "DataEngineering",
      "Docker",
      "Azureplatform",
      "Databricks",
      "AzureMLservices",
      "Git",
      "JupyterNotebooks",
      "GCPplatform",
      "GoogleBigquery",
      "Php",
      "codeignitorframework",
      "javascript",
      "html",
      "css",
      "bootstrap",
      "MS-SQL",
      "MySQL",
      "SQLite",
      "MongoDB",
      "BigQuery",
      "Numpy",
      "SciPy",
      "Pandas",
      "Dask",
      "GeoPandas",
      "Sklearn",
      "NLTK",
      "OpenCV",
      "Keras",
      "Tensorflow",
      "AzureML",
      "Pytorch",
      "AzureMLStudio",
      "GCPAIPlatform",
      "AWSSagemaker",
      "Kubeflow",
      "Flask",
      "Plotly",
      "Matplotlib",
      "Seaborn",
      "GoogleCloudPlatform(GCP)",
      "Azure",
      "AWS",
      "GoogleColab",
      "Heroku",
      "JupyterNotebook",
      "Github",
      "VSCodeIDE",
      "MachineLearningAlgorithms",
      "DeepLearningTechinques"
    ]
    
   \n\nJD:\n
   Senior Data Scientist (Backend & Advanced Databases)

Location: [Your Location]
Type: Full-Time
Experience: 5+ Years

About Us:
We are an innovative technology company committed to leveraging data-driven insights to transform business outcomes. We are seeking a highly skilled Senior Data Scientist with strong backend development experience and expertise in advanced databases to join our dynamic team.

Key Responsibilities:

Design, develop, and deploy scalable data science solutions that integrate with backend systems.

Build and maintain data pipelines to extract, transform, and load (ETL) large volumes of structured and unstructured data.

Collaborate with engineering teams to integrate machine learning models into production systems.

Optimize and manage advanced databases, including NoSQL and distributed databases, for high-performance data access.

Develop and maintain APIs and backend services supporting data-driven applications.

Analyze large datasets to extract actionable insights and build predictive models.

Mentor junior data scientists and collaborate cross-functionally with product, engineering, and business teams.

Required Qualifications:

Bachelor’s or Master’s degree in Computer Science, Data Science, Statistics, or related field.

5+ years of experience in data science, machine learning, or analytics roles.

Strong programming skills in Python, Java, or similar backend languages.

Experience with backend frameworks (e.g., Flask, Django, Spring).

Expertise in SQL and advanced databases such as PostgreSQL, MongoDB, Cassandra, or similar.

Experience with distributed databases and big data technologies (e.g., Hadoop, Spark).

Familiarity with cloud platforms (AWS, GCP, Azure) and containerization (Docker, Kubernetes).

Solid understanding of data structures, algorithms, and software engineering best practices.

Excellent problem-solving skills and ability to work in a fast-paced environment.

Preferred Skills:

Experience deploying ML models with REST APIs or microservices.

Knowledge of data warehousing and ETL tools.

Familiarity with CI/CD pipelines and DevOps practices.

Experience with visualization tools like Tableau, Power BI, or similar.

What We Offer:

Competitive salary and benefits package.

Opportunity to work on cutting-edge technologies and large-scale data projects.

Collaborative and inclusive work environment.

Career growth and continuous learning opportunities."""
)

def get_rank_from_ollama(prompt) -> str:
    """
    Call local Ollama model to get ranking score + explanation.
    Assumes Ollama is running locally on port 11434.
    """
    try:
        response = completion(
            model="ollama/llama3.2:3b",
            messages=[{"role": "user", "content": prompt}],
            api_base="http://localhost:11434"
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling Ollama model: {e}"
    
print(get_rank_from_ollama(prompt=prompt))