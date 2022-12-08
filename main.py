import base64
import json
import os
import re
import requests
import openai
import urllib.request
from bs4 import BeautifulSoup
from PIL import Image

# Set the WordPress credentials
username = ""
password = ""

# Store OpenAI API Key
openai.api_key = ""


# Create the Basic Auth string
auth_string = f"{username}:{password}"
base64_auth_string = base64.b64encode(auth_string.encode("utf-8"))
auth_header = f"Basic {base64_auth_string.decode('utf-8')}"

# Set the headers for the POST request
headers = {
    "Content-Type": "application/json",
    "Authorization": auth_header
}

# Set the endpoint URL for uploading images
upload_endpoint_url = "http://example.com/wp-json/wp/v2/media"

# Set the endpoint URL for creating posts
post_endpoint_url = "http://example.com/wp-json/wp/v2/posts"

# Define the function for generating essays using GPT-3
def generate_essay(prompt, model="text-davinci-002"):
  response = openai.Completion.create(
      engine=model,
      prompt=prompt,
      temperature=0.5,
      max_tokens=1024,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
  )

  return response["choices"][0]["text"]

# Define the function for generating images using DALL-E 2
def generate_image(title):
  image = openai.Image.create(
    prompt=title,
    n=1,
    size="256x256"
  )
  image_url = image['data'][0]['url']

  return image_url

# Define the function for uploading an image
def upload_image(imgPath):
    # Open the file and read it into memory
    data = open(imgPath, 'rb')
    file_contents = data.read()

    # Close the file after it has been read
    data.close()

    fileName = os.path.basename(imgPath)
    res = requests.post(url=upload_endpoint_url,
                        data=file_contents,
                        headers={ 'Content-Type': 'image/jpg','Content-Disposition' : 'attachment; filename=%s'% fileName},
                        auth=(username, password))
    newDict=res.json()
    newID= newDict.get('id')
    link = newDict.get('guid').get("rendered")
    print(newID, link)
    return newID

def create_post(title, content, media):
    url = "https://example.com/wp-json/wp/v2/posts"

    # Upload the image using the file path
    image_id = upload_image(media)

    # Get the file name from the file path
    file_name = os.path.basename(media)

    # Set the post title to the file name
    title = file_name

    payload = {
    "title": title,
    "content": content,
    "featured_media": image_id,
    "status": "publish"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        print("Post created successfully")
    else:
        print(f"Error creating Post {response.status_code}")

    return response.status_code

def get_news():
    # Set the URL of the tech news website
    url = "https://www.techradar.com/news"

    # Send a GET request to the website
    response = requests.get(url)

    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the elements on the page that contain the tech news articles
    articles = soup.find_all(class_="feature-block-item-wrapper")

    # Set the number of articles to process
    num_articles = 3

    # Create an iterator to keep track of how many articles have been processed
    i = 1

    # Use a while loop to process a limited number of articles
    while i < num_articles:
    # Use a try/except block to handle the IndexError gracefully
        try:
            # Get the current article
            article = articles[i]

            # Get the title and URL of the article
            title = article.find(class_="article-name").text
            url = article.find("a").get("href")

            # Send a GET request to the article page
            article_response = requests.get(url)

            # Parse the HTML content of the article page
            article_soup = BeautifulSoup(article_response.content, "html.parser")

            # Find the elements on the page that contain the article content
            article_content = article_soup.find_all("p")

            # Extract the text of the article content
            content = "\n".join([p.text for p in article_content][1:8] + [p.text for p in article_content][9:10])

            # Generate an essay for the article
            essay_prompt = f"Write a long form article or blog post that describes the opposite about this:\n{content}"
            generated_essay = generate_essay(essay_prompt)
            title_prompt = f"write a short title for the article:\n{generated_essay}"
            generated_title = generate_essay(title_prompt)
            generated_title = generated_title[2:]
            file_name = re.sub(r"[^\w\s-]", "-", generated_title)

            image = generate_image(file_name)
            
            # Get the current working directory
            cwd = os.getcwd()      
            
            image_path, _ = urllib.request.urlretrieve(image, file_name + ".jpg")
            image = Image.open(image_path)
            print(image_path)

            # Create the "articles" folder if it does not already exist
            if not os.path.exists(os.path.join(cwd, "articles")):
                os.makedirs(os.path.join(cwd, "articles"))

            try:
                # Open a new file in write mode
                with open(os.path.join(cwd, "articles", file_name), "w") as file:
                    # Write the essay to the file
                    file.write(generated_essay)

                with open(os.path.join(cwd, "articles", file_name), "r") as file:
                    # Get the file name and content
                    title = file.name
                    content = file.read()

            # Create a new WordPress post using the file name and content
                create_post(title, content, image_path)
            except FileNotFoundError:
                print("Error creating file: ", file_name)
        except IndexError:
            print("Not enough articles. ")

        i += 1

get_news()
