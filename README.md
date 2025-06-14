# Food Facilities Challenge

MOST IMPORTANTLY 

Github Repo: https://github.com/eyc7/food-facilities-challenge 

Served on Google Cloud Frontend Test here: https://food-frontend-688153142575.us-central1.run.app/
<img width="1728" alt="Screenshot 2025-06-14 at 2 05 51 PM" src="https://github.com/user-attachments/assets/742c4144-ef67-4726-95d7-a82210a71b8c" />

Backend hosted: https://my-flask-app-688153142575.us-central1.run.app/


Use this data set about Mobile Food Facilities in San Francisco (https://data.sfgov.org/Economy-and-Community/Mobile-Food-Facility-Permit/rqzj-sfat/data) to build an application. Please clarify with your recruiter first if you will be doing the Backend Focused or Frontend Focused version of the project, and what language you will be doing the challenge in. Make sure this is clear before you start this challenge.

**Backend Focused Version**

Your Application should have the following features:
- Search by name of applicant. Include optional filter on "Status" field.
- Search by street name. The user should be able to type just part of the address. Example: Searching for "SAN" should return food trucks on "SANSOME ST"
- Given a latitude and longitude, the API should return the 5 nearest food trucks. By default, this should only return food trucks with status "APPROVED", but the user should be able to override this and search for all statuses.
  - You can use any external services to help with this (e.g. Google Maps API).
- We write automated tests and we would like you to do so as well.

*Bonus Points:*
- Use an API documentation tool
- Provide a dockerfile with everything necessary to run your application (for backend focused candidates)
- Build a UI

**Frontend Focused Version**

Your application should have the following features:
- Search by name of applicant. Include optional filter on "Status" field.
- Search by street name. The user should be able to type just part of the address. Example: Searching for "SAN" should return food trucks on "SANSOME ST"
- Build a UI using a frontend framework like React. You have creative freedom to design the UI however you would like.

*Bonus points:*
- Write automated tests
- Use an API documentation tool
- Build the other features listed in the Backend Focused Version

## README

Your code should include a README file including the following items:

- Description of the problem and solution;
- Reasoning behind your technical/architectural decisions
- Critique section:
  - What would you have done differently if you had spent more time on this?
  - What are the trade-offs you might have made?
  - What are the things you left out?
  - What are the problems with your implementation and how would you solve them if we had to scale the application to a large number of users?
- Please document any steps necessary to run your solution and your tests.

## How we review

We value quality over feature-completeness. It is fine to leave things aside provided you call them out in your project's README.
The aspects of your code we will assess include:

- Clarity: does the README clearly and concisely explains the problem and solution? Are technical tradeoffs explained?
- Correctness: does the application do what was asked? If there is anything missing, does the README explain why it is missing?
- Code quality: is the code simple, easy to understand, and maintainable? Are there any code smells or other red flags? Does object-oriented code follows principles such as the single responsibility principle? Is the coding style consistent with the language's guidelines? Is it consistent throughout the codebase?
- Security: are there any obvious vulnerabilities?
- Technical choices: do choices of libraries, databases, architecture etc. seem appropriate for the chosen application?

## What to send back to our team
Please send an email back to your point of contact with a compressed (zip) file of your Github project repo when done.



# Setting up the project. 
- I opted to use python flask as a quick python server that I can spin up for ease of testing and plenty of documentation. Some tools I use for testing is postman to hit my APIs quickly. 
- Database choice: PostgreSQL for as it's one of the most feature rich open source relational database and its supports PostGIS for geo data.

- using ```psql -d easonchang -c "\copy mobile_food_facility_permit FROM 'Mobile_Food_Facility_Permit.csv' CSV HEADER"``` we can quickly turn our csv into a database table named mobile_food_facility_permit

- Wrote a few sql queries to search by name and street name

- map these sql queries to API endpoint

- curl -X POST http://127.0.0.1:5000/search_applicant \
     -H "Content-Type: application/json" \
     -d '{"applicant": "food"}'

- curl -X POST http://127.0.0.1:5000/search_applicant \
  -H "Content-Type: application/json" \
  -d '{
        "applicant": "taco",
        "status": ["APPROVED", "REQUESTED"],
      }'
```
[
    {
        "address": "3119 ALEMANY BLVD",
        "applicant": "San Pancho's Tacos",
        "latitude": 37.71019301997575,
        "longitude": -122.4552219061259,
        "status": "APPROVED",
        "zipcodes": "28861"
    },
    {
        "address": "1271 CAPITOL AVE",
        "applicant": "San Pancho's Tacos",
        "latitude": 37.724297778527635,
        "longitude": -122.45937730954839,
        "status": "APPROVED",
        "zipcodes": "28861"
    },
    {
        "address": "491 BAY SHORE BLVD",
        "applicant": "San Pancho's Tacos",
        "latitude": 0.0,
        "longitude": 0.0,
        "status": "APPROVED",
        "zipcodes": null
    }
]
```

- While I decided to keep the other functionalities all within /search_applicant. I decided to separate out the business logic for search nearby in to a separate endpoint due to the complexity and it doesn't share to many business logics with the other functionalities. 

- I chose to use the **Google Distance Matrix API** instead of implementing distance calculations directly in PostGIS because the latter can be complex and time-consuming to set up, especially if you want highly accurate travel distances and durations. The Google API provides a convenient, reliable way to get real-world driving or walking distances based on actual routes rather than just straight-line distances.

**However, the Google Distance Matrix API free tier has some limitations:**

- You can only make a limited number of requests per day (usually around 100).
- Each request supports a maximum of **25 origins and 25 destinations**, meaning you can only send up to 25 latitude-longitude pairs at a time. 
- If your use case requires processing large batches of locations or frequent requests, you may quickly hit these limits and need to pay for higher usage.

- We needed to get creative and batch process these. Would not be sustainable if our datasets are bigger.

**Building your own solution using PostGIS and PostgreSQL, while initially more complex, offers several advantages:**

- Full control without external API rate limits or costs.
- Ability to perform spatial queries on an unlimited number of locations.
- Support for custom logic and integration with your data model.
- Optimization opportunities with spatial indexing for better performance.

In summary, the Google Distance Matrix API offers quick and easy setup with realistic travel distances but has usage limitations that might not scale for large or high-frequency applications. Building your own distance calculations using PostGIS is more complex but ultimately more robust and scalable for larger or custom requirements.



- curl -X POST http://127.0.0.1:5000/search_nearby \
-H "Content-Type: application/json" \
-d '{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "statuses": ["APPROVED", "EXPIRED"]
}'

```
[
    {
        "address": "150 OTIS ST",
        "applicant": "Brazuca Grill",
        "distance_km": 0.54,
        "latitude": 37.770683395042624,
        "longitude": -122.42087956139908,
        "status": "APPROVED",
        "zipcodes": "28853"
    },
    {
        "address": "1455 MARKET ST",
        "applicant": "Bay Area Mobile Catering, Inc. dba. Taqueria Angelica's",
        "distance_km": 0.6,
        "latitude": 37.77522830783405,
        "longitude": -122.41746613186956,
        "status": "APPROVED",
        "zipcodes": "28853"
    },
    {
        "address": "1690 FOLSOM ST",
        "applicant": "Mini Mobile Food Catering",
        "distance_km": 0.78,
        "latitude": 37.77013758050153,
        "longitude": -122.41598340280362,
        "status": "EXPIRED",
        "zipcodes": "28853"
    },
    {
        "address": "1501 FOLSOM ST",
        "applicant": "Bay Area Mobile Catering, Inc. dba. Taqueria Angelica's",
        "distance_km": 0.81,
        "latitude": 37.771586702670334,
        "longitude": -122.41400704302406,
        "status": "APPROVED",
        "zipcodes": "28853"
    },
    {
        "address": "355 11TH ST",
        "applicant": "Mini Mobile Food Catering",
        "distance_km": 0.91,
        "latitude": 37.77146721590103,
        "longitude": -122.41287229420975,
        "status": "EXPIRED",
        "zipcodes": "28853"
    }
]
```


- This batch processing has pretty high latency at 500 records. Any higher, we would need to build out a custom solution using PostGIS and PostgreSQL, which is the exact reason that I picked this relational database. Some possible solutions is caching results for a longitude and latitude and/or concurrently make the API calls.



Then do all this in google cloud to host frontend react app, bakcend flask app, and the postgreSQL instance.




- curl -X POST "https://my-flask-app-688153142575.us-central1.run.app/search_applicant" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant": "taco",
    "statuses": ["APPROVED"]
  }'


- curl -X POST "https://my-flask-app-688153142575.us-central1.run.app/search_nearby" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 37.7749,
    "longitude": -122.4194,
    "statuses": ["APPROVED"]
  }'

