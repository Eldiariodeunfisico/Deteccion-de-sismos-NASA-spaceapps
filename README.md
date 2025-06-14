# Seismic Detection Across the Solar System Challenge

Today, we challenge YOU to parse through seismic data collected on the Moon and Mars and figure out how to detect moonquakes and marsquakes! 
To get you started on the data, we present to you a training set containing the following:

1. A catalog of quakes identified in the data
2. Seismic data collected by the Apollo (one day segments) or InSight (one hour segments) missions in miniseed and CSV format. 
3. Plots of the trace and spectrogram for each day a quake has been identified. 

Using these tools, your task is to come up with an algorithm to identify these signals (using the catalog as a benchmark) and then 
apply your algorithm to the seismic data in the "test" folder (Apollo 12, 15, and 16 for the Moon and other InSight events for Mars). 

Each trace included in the test folder has a quake in it, there are no empty traces. 

This main folder also has a Jupyter notebook that will help you get started on the data.

[Ver presentación del proyecto](https://gamma.app/docs/Seismic-Detection-across-the-Solar-System-p3jqenybesmv7nw?mode=doc)

# IMPORTANT
Please make sure that your output catalog has at least the following headers:
filename
time_abs(%Y-%m-%dT%H:%M:%S.%f) or time_rel(sec)

If not, your output catalog may not be scored!!

Good luck!!! If you have any questions, our team leaders will be around to help during the hackathon weekend!  

# LINK where you can see and analyze all the data using the different algorithms

https://the-outlier-society-hackaton.com/

<iframe src="https://the-outlier-society-hackaton.com/" width="100%" height="500px" style="border:none;"></iframe>

# To Run the project internally, you must do the following:

1. Clone this repo.

```Bash
curl --location https://wufs.wustl.edu/SpaceApps/data/space_apps_2024_seismic_detection.zip --output space_apps.zip
unzip space_apps.zip
mv space_apps_2024_seismic_detection/* .
rm -rf space_apps_2024_seismic_detection/
conda create --prefix ./.env python=3.11 -y
conda activate ./.env
python3 pip install -r requirements.txt
streamlit run app.py
```
2. Go to your localhost:8501

# Detecciones:

1. The detections are in the Simos_Luna.csv file and Simos_Marte.csv
