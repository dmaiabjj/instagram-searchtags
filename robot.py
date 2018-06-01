import requests, json, logging, os, errno, random, chronos
from transform import RGBTransform
from PIL import Image

# DEBUG: Detailed information, typically of interest only when diagnosing problems.

# INFO: Confirmation that things are working as expected.

# WARNING: An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.

# ERROR: Due to a more serious problem, the software has not been able to perform some function.

# CRITICAL: A serious error, indicating that the program itself may be unable to continue running.

logging.basicConfig(filename='./logs/insta_bot.log', level=logging.ERROR,format='%(asctime)s:%(levelname)s:%(message)s')
logger      = logging.getLogger(__name__)


def generate_image(tup):
    try:
        tags = [("vermelho",(255,0,0)),("laranja",(255,69,0)),("amarelo",(255,255,0)),("verde",(0,128,0)),("azul",(0,0,255)),("violeta",(128,0,128))]
        response  = requests.get(tup["image_url"]) 
        if response.status_code == 200:
            for tag,color in tags:
                if(tag in tup["text"].lower()):
                   directory      = "./images/{0}/".format(tup["username"])
                   file_name      = "{0}_{1}.jpg".format(tup["id"],tag)
                   save_image(directory,file_name,response.content,color)
    
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise
    except Exception as e:
        logger.exception(str(e)) 

def save_image(directory,file_name,content,color):
    if not os.path.exists(os.path.dirname(directory)):
        os.makedirs(os.path.dirname(directory))
       
    path = directory+file_name
    with open(path, 'wb') as f:
        f.write(content)                 
    
    image_tint = RGBTransform().mix_with(color,factor=.40).applied_to(Image.open(path))   
    image_tint.save(path)

def get_user_name(shortcode):
    user_name = "unknown_user"
    try:
        search_url   = "https://www.instagram.com/p/{0}/?__a=1".format(shortcode)
        response     = requests.get(search_url)
        js           = json.loads(response.text)
    except Exception as e:
        logger.exception(str(e))
    finally:
        if js:
            user_name   = js["graphql"]["shortcode_media"]["owner"]["username"]
        return user_name

def get_tag_results(tag,has_next_page,end_cursor=""):
    js      = ""
    results = ()
    try:
        url_pattern  = "https://www.instagram.com/explore/tags/{0}/?__a=1&max_id={1}"
        search_url   = url_pattern.format(tag,end_cursor)
        response     = requests.get(search_url)
        js           = json.loads(response.text)
    except Exception as e:
        logger.exception(str(e))
    finally:
        if js:
            has_next_page   = js["graphql"]["hashtag"]["edge_hashtag_to_media"]["page_info"]["has_next_page"]
            end_cursor      = js["graphql"]["hashtag"]["edge_hashtag_to_media"]["page_info"]["end_cursor"]
            results         = list(js["graphql"]["hashtag"]["edge_hashtag_to_media"]["edges"])
        else:
            has_next_page   = False
            end_cursor      = ""
            results         = ()
            

        return (has_next_page,end_cursor,results)


def search():
    print("JOB WAS INITIALIZED")
    tag             = "ACORQUEMEREPRESENTA"
    has_next_page   = True
    end_cursor      = ""

    while has_next_page:
        has_next_page,end_cursor,nodes = get_tag_results(tag,has_next_page,end_cursor)
        for node in nodes:
            generate_image({"id" : node["node"]["id"],"username" : get_user_name(node["node"]["shortcode"]),"image_url" : node["node"]["display_url"],"text":node["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]})




def init():
    # bind a ioloop or use default ioloop
    chronos.setup()  # chronos.setup(tornado.ioloop.IOLoop())
    chronos.schedule('search', chronos.every(2).hours, search)
    chronos.start(True)

if __name__ == '__main__':
    init()