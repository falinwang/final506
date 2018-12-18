# FINAL PROJECT README
## SI 506 Programming I (Python)
Name: Roy Wang
Date: 2018/12/17

### 1. Project Description
My project focus on making use of APIs on Ticketmaster and iTunes.
This project will search for recent "concert" by postal code (default will be "48104") with Ticketmaster API and get the artists who will perform in the concert, the date, time and link of the concert. Then, it will search the details of the 10 most recent songs of artists who will perform in the concert with iTunes research API.

### 2. The files included in this project
1. **README.pdf**
2. **SI506F18_final_project.py** is a python file that should be used to run the program
3. **Sample_event_media.CSV** is provided as a sample file produces by this project

### 3. The Python Modules I am Importing in the File
1. requests
2. json
3. csv: to create a csv file
4. sys: to resolve the encoding problem

### 4. How to Run the Project
1. Make sure you are running Python 3
2. Download the file "SI506F18_final_project.py"
3. Enter the following command line in your terminal to run the code:
`python SI506F18_final_project.py`
4. It will show an input prompt says: 
`To search the concert near you, enter 5 digits postal code (eg. 48104): `
	1. Enter 5 digits postal code in the USA. Here are some samples you can try to input: 
		1. 48104
		2. 10001
		3. 43001
	2. If there’s no result for the postal code you search, the program will prompt you again.
	3. If successful, it will create a CSV file for you.

### 5.  The Result of Program
Once the program runs successfully, in the same directory you should find a CSV file called `event_media.CSV`.
The first part of the file have five columns, containing information about the name, date, time, lineup, and link of the concert and the second part of the file have five five columns, containing information about the artist name, track title, album title, length, and release date of each song. There will be ten songs for each artist performing in the concerts and the songs are sorted by the release date from latest to oldest.

### 6. Requirement List
* Cache all data
	* Make a search on Ticketmaster (accessing and caching data): 107-128 
	* Make a search on iTunes API (accessing and caching data): 226-245
* Retrieve data from 2 different API endpoints: 153, 261
* Include at least 2 function definitions
	* `def params_unique_combination`: 20
	* `def get_event_data_with_caching`: 107
	* `def get_artist_songs_with_caching`: 226
* Include at least 2 class definitions
	* Class TicketmasterEvent: 52
	* Class ITunesMedia: 195
* Create at least 1 instance of each class
	* Class TicketmasterEvent: 55-61
	* Class ITunesMedia: 198-202
* Invoke methods on them: 84, 170, 213, 283, 288
* Accumulate data: 57, 157, 266, 271
* Write data to a CSV file: 280
