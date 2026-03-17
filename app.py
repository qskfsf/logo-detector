import cv2
import numpy as np
import requests
import os
import imagehash
from PIL import Image
from flask import Flask, request, jsonify

app = Flask(__name__)

logo_templates=[]
image_hashes=[]

logo_folder="logos"
image_folder="images"

# تحميل الشعارات
for file in os.listdir(logo_folder):
    path=os.path.join(logo_folder,file)
    logo=cv2.imread(path,0)
    if logo is None:
        continue
    logo_templates.append(logo)

# تحميل الصور الكاملة
for file in os.listdir(image_folder):
    path=os.path.join(image_folder,file)
    try:
        h=imagehash.phash(Image.open(path))
        image_hashes.append(h)
    except:
        pass


@app.route("/check",methods=["POST"])
def check():

    data=request.json

    if not data or "image" not in data:
        return jsonify({"logo":False})

    url=data["image"]

    try:
        r=requests.get(url,timeout=10)
    except:
        return jsonify({"logo":False})

    img_array=np.asarray(bytearray(r.content),dtype=np.uint8)
    img=cv2.imdecode(img_array,cv2.IMREAD_GRAYSCALE)

    if img is None:
        return jsonify({"logo":False})

    # فحص الشعار
    for logo in logo_templates:

        for scale in np.linspace(0.3,1.5,20):

            resized=cv2.resize(logo,None,fx=scale,fy=scale)

            if resized.shape[0] > img.shape[0] or resized.shape[1] > img.shape[1]:
                continue

            result=cv2.matchTemplate(img,resized,cv2.TM_CCOEFF_NORMED)

            (_,maxVal,_,_)=cv2.minMaxLoc(result)

            if maxVal > 0.88:
                return jsonify({"logo":True})

    # فحص الصور الكاملة
    try:
        img_hash=imagehash.phash(Image.open(requests.get(url,stream=True).raw))
    except:
        return jsonify({"logo":False})

    for h in image_hashes:

        if abs(img_hash-h) < 8:
            return jsonify({"logo":True})

    return jsonify({"logo":False})


if __name__=="__main__":
    import os
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
