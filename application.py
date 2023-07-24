#loading all required libraries
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup as bs
from flask_cors import CORS, cross_origin
import requests
from urllib.request import urlopen
import logging
import pymongo

#creating a log ile
logging.basicConfig(filename = 'scrap.log', 
                    level = logging.INFO, 
                    format = '%(name)s %(levelname)s %(message)s ')

application = Flask(__name__)
app = application

#creating main landing page
@app.route('/',methods = ['GET'])
@cross_origin()
def homepage():
    return render_template("index.html")

#creating /review page
@app.route('/review', methods = ['POST','GET'])
@cross_origin()
def index():
    if request.method=='POST':
        try:
            #search string entered by user
            searchString = request.form['content'].replace(" ","")
            #creating link
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            #open link page
            urlClient = urlopen(flipkart_url)
            #reading the page content
            flipkartPage = urlClient.read()
            urlClient.close()
            #using beautiful soap to make the content in html readable format
            flipkart_html = bs(flipkartPage,'html.parser')
            #list of all products showing on landing page
            bigbox = flipkart_html.find_all("div",{"class":"_1AtVbE col-12-12"})
            #deleting first three div's
            del bigbox[0:3]
            #storing first product link
            product_link = "https://www.flipkart.com"+bigbox[0].div.div.div.a['href']
            #get request for product link
            prodReq = requests.get(product_link)
            #utf-8 encoding
            prodReq.encoding = 'utf-8'
            #using beautiful soap to make the content in html readable format
            prodHtml = bs(prodReq.text,'html.parser')
            #selecting div  all reviews
            prodAll = prodHtml.find_all('div',{'class':'col JOpGWq'})
            #storing link for all reviews page
            reviewAll = "https://www.flipkart.com" + prodAll[0].find_all('a')[-1]['href']
            #reading the page content for all reviews page
            reviewPage = bs(requests.get(reviewAll).text,'html.parser')
            #list of review pages 1-10
            revPageList = reviewPage.find_all("a",{"class":"ge-49M"})
            
            #creating a csv file 
            filename = searchString + ".csv"
            fw = open(filename, "w")
            #storing info in file 
            headers = "Product, Customer Name, Rating, Heading, Comment \n"
            fw.write(headers)
            #creating a list to append the data
            reviews = []
            
            #looping over review pages 1-10
            for i in revPageList:
                try:
                    #reading page content for each review page
                    pageLink = bs(requests.get("https://www.flipkart.com"+i['href']).text,'html.parser')
                    #list of all comment div on the page
                    commentBoxes = pageLink.find_all('div',{'class':'_1AtVbE col-12-12'})
                    #deleting first 4 and last div
                    del commentBoxes[0:4]
                    del commentBoxes[-1]
                except:
                    logging.error("Review page link issue")
                    
                try:
                    #looping over all the comments on the page
                    for commentbox in commentBoxes:
                        try:
                            #user name
                            name = commentbox.div.div.find_all('p',{'class':'_2sc7ZR _2V5EHH'})[0].text
                        except:
                            logging.error("Name not found")
                        try:
                            #review heading
                            heading = commentbox.div.find_all('p',{'class':'_2-N8zT'})[0].text
                        except:
                            logging.error("No heading")
                        try:
                            #review rating
                            rating = commentbox.div.div.find_all('div',{'class':'_3LWZlK _1BLPMq'})[0].text
                        except:
                            logging.error("No rating")
                        try:
                            #review comment
                            custComment = commentbox.div.find_all('div',{'class':'t-ZTKy'})[0].div.div.text
                        except:
                            logging.error("No customer comment")
                            
                        #storing info in a dictionary
                        mydict = {"Product": searchString,"Name":name, "Rating":rating,"CommentHead":heading,
                                 "Comment":custComment}
                        #adding in list reviews
                        reviews.append(mydict)
                    
                except Exception as e:
                    logging.error("Error in comment box ")
            
            #logging all reviews
            logging.info("Log my final result {}".format(reviews))
                
            #connecting to mongodb
            client = pymongo.MongoClient("mongodb+srv://theserenecoder:Mukesh90@cluster0.kimqlv5.mongodb.net/?retryWrites=true&w=majority")
            
            #creating a database
            db = client["flipkartScrap"]
            
            #creating collection in our database
            reviewColl = db["flipkartScrapData"]
            
            #inserting data in our collection
            reviewColl.insert_many(reviews)
            
            return render_template('result.html',reviews = reviews[0:(len(reviews)-1)])
        
        except Exception as e:
            logging.error('The exception message is : ', e)
            return 'something is wrong {}'.format(e)
    else:
        return render_template('index.html')
    
if __name__ == '__main__':
    app.run(host='127.0.0.1',port=8000)
