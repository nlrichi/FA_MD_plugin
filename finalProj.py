import os
import base64
import logging
import tempfile
import shutil
import cv2
import numpy as np
import ssl
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from feat import Detector
from PIL import Image
import imageio
from scipy.spatial import Delaunay
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


BASE_DIR = os.path.dirname(__file__)
PLUGIN_DIR = os.path.join(BASE_DIR, 'roundcubemail', 'plugins', 'mood_plugin')

app = Flask(__name__, template_folder=PLUGIN_DIR, static_folder=PLUGIN_DIR, static_url_path='/plugins/mood_plugin')
CORS(app, resources={r"/*": {"origins": "/http://localhost:8000"}})

pyfeat_detector = Detector()  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
temp_dir = tempfile.mkdtemp()

CERT_FILE = os.path.join(BASE_DIR, 'cert.pem')
KEY_FILE = os.path.join(BASE_DIR, 'key.pem')

# Generate self-signed certificate
def generate_self_signed_cert(cert_path, key_path):
    # Generate a private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    # write the private key to a file
    with open(key_path, "wb") as key_file:
        key_file.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
            
        ))
    # issuer details
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"UK"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"London"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"London"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Mood Plugin"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])
    # Create a self-signed certificate
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())    
    )
    # Write the certificate to a file
    with open(cert_path, "wb") as cert_file:
        cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
    
# Check if certificate and key files exist, if not generate them
if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
    generate_self_signed_cert(CERT_FILE, KEY_FILE)
    logger.info(f"Generated self-signed certificate at {CERT_FILE} and key at {KEY_FILE}")
else:
    logger.info(f"Certificate and key already exist at {CERT_FILE} and {KEY_FILE} reusing...")

#Prepare SSL context
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

def detect_emotions(image_path):
    try:
        # Detects emotions in the image using py-feat and returns the dominant emotion    
        df = pyfeat_detector.detect_image(image_path)
        if df is None or df.empty:
            logger.warning(f"No face detected in {image_path}")
            return None
        # returns the emotion with the highest score
        dominant_emotion = df.emotions.iloc[0].idxmax()
        logger.info(f"Detected dominant emotion in  {image_path}: {dominant_emotion}")
        return dominant_emotion
    except Exception as e:
        logger.error(f"Error in emotion detection: {str(e)}")
        return None

def animate_expression(img1_path, img2_path):
    """Creates a morphing animation between two images.""" 

    pil1 = Image.open(img1_path)
    pil2 = Image.open(img2_path)
    W, H = pil1.size
    pil2_res = pil2.resize((W, H), Image.LANCZOS)
    
    # Save resized versions for py-feat
    res1_path = os.path.join(temp_dir, "face1_resized.jpg")
    res2_path = os.path.join(temp_dir, "face2_resized.jpg")
    pil1.save(res1_path)
    pil2_res.save(res2_path)

    rgb1 = np.array(pil1)
    rgb2 = np.array(pil2_res)
    
    fex1 = pyfeat_detector.detect_image(res1_path)
    fex2 = pyfeat_detector.detect_image(res2_path)
    
    # Check if faces were detected using RetinaFace
    if fex1 is None or fex2 is None or fex1.empty or fex2.empty:
        logger.warning("Face detection failed in one or both images")
        raise ValueError("No face detected in one or both images. Please ensure good lighting and clear faces.")
    
    # Get landmarks from results and reshape
    lm1 = fex1.landmarks.iloc[0].values.reshape(-1, 2)
    lm2 = fex2.landmarks.iloc[0].values.reshape(-1, 2)
    os.remove(res1_path)
    os.remove(res2_path)
    
    # Add Corners & Triangulate
    corners = np.array([[0,0],[W,0],[W,H],[0,H]])
    pts1 = np.vstack([lm1, corners])
    pts2 = np.vstack([lm2, corners])
    
    mean_pts = (pts1 + pts2) / 2
    tri = Delaunay(mean_pts)
    triangles = tri.simplices

    # gif file size restrictor
    def optimize_for_gif(image, max_size_mb=1.5):
        img_size = image.nbytes / (1024 * 1024)
        
        if img_size <= max_size_mb:
            return image
            
        # Calculate scale factor needed
        scale = np.sqrt(max_size_mb / img_size)  
        h, w = image.shape[:2]
        new_h = int(h * scale)
        new_w = int(w * scale)
        
        # Resize using area interpolation for better quality
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized

    rgb1 = optimize_for_gif(rgb1)
    rgb2 = optimize_for_gif(rgb2)
    
    
    img_size_mb = rgb1.nbytes / (1024 * 1024)
    n_frames = min(10, max(5, int(20 / img_size_mb)))  
    duration = max(0.1, 0.2 - (img_size_mb / 10))  
    
    # Warp Function
    def warp_image(img, src_pts, dst_pts, triangles):
        H_img, W_img, _ = img.shape
        canvas = np.zeros_like(img)
        for tri_idxs in triangles:
            t_src = src_pts[tri_idxs]; t_dst = dst_pts[tri_idxs]
            if t_src.shape != (3,2) or t_dst.shape != (3,2):
                continue
            if abs(cv2.contourArea(t_dst.astype(np.float32))) < 1e-4:
                continue

            t_src = t_src.astype(np.float32)
            t_dst = t_dst.astype(np.float32)
            x_s,y_s,w_s,h_s = cv2.boundingRect(t_src)
            x_d,y_d,w_d,h_d = cv2.boundingRect(t_dst)
            if w_s<1 or h_s<1 or w_d<1 or h_d<1:
                continue

            src_sub = t_src - [x_s,y_s]
            dst_sub = t_dst - [x_d,y_d]
            patch = img[y_s:y_s+h_s, x_s:x_s+w_s]

            try:
                M = cv2.getAffineTransform(src_sub, dst_sub)
                warped = cv2.warpAffine(patch, M, (w_d,h_d),
                                        flags=cv2.INTER_LINEAR,
                                        borderMode=cv2.BORDER_REFLECT_101)
            except cv2.error:
                continue

            mask = np.zeros((h_d, w_d, 3), dtype=np.uint8)
            cv2.fillConvexPoly(mask, np.int32(dst_sub), (1,1,1))

            # Crop to canvas bounds
            x_end = min(x_d + w_d, W_img)
            y_end = min(y_d + h_d, H_img)
            w_eff = x_end - x_d
            h_eff = y_end - y_d
            if w_eff<=0 or h_eff<=0:
                continue

            canvas[y_d:y_end, x_d:x_end] += warped[:h_eff, :w_eff] * mask[:h_eff, :w_eff]

        # Fill holes
        empty = (canvas.sum(axis=2)==0)
        canvas[empty] = img[empty]
        return canvas
    
    # Generate Morph Frames
    frames = []
    
    for i in range(n_frames):
        alpha = i / (n_frames - 1)
        # Interpolate shapes toward mean
        inter1 = (1-alpha)*pts1 + alpha*mean_pts
        inter2 = (1-alpha)*pts2 + alpha*mean_pts
    
        w1 = warp_image(rgb1, pts1, inter1, triangles)
        w2 = warp_image(rgb2, pts2, inter2, triangles)
    
        # Cross-dissolve
        morphed = ((1-alpha)*w1 + alpha*w2).astype(np.uint8)
        frames.append(morphed)
    
    #reverse animation back to start
    frames += frames[-2:0:-1]
    
    # Save the animation with strict file size limit
    output_gif = os.path.join(temp_dir, "face_morph.gif")
    max_bytes = 2 * 1024 * 1024 

    # Helper to save and check size
    def save_gif_and_check(frames, duration, path):
        imageio.mimsave(
            path,
            frames,
            duration=duration,
            loop=0,
            optimize=True,
            quantizer='nq'
        )
        return os.path.getsize(path)

    current_frames = frames
    current_duration = duration
    current_size = save_gif_and_check(current_frames, current_duration, output_gif)


    while current_size > max_bytes:
        if len(current_frames) > 5:
            current_frames = current_frames[::2]  # Drop every other frame
        else:
            # Reduce resolution by 10%
            new_frames = []
            for f in current_frames:
                h, w = f.shape[:2]
                new_h = int(h * 0.9)
                new_w = int(w * 0.9)
                if new_h < 32 or new_w < 32:
                    break 
                new_frames.append(cv2.resize(f, (new_w, new_h), interpolation=cv2.INTER_AREA))
            if new_frames:
                current_frames = new_frames
            else:
                break 
        current_size = save_gif_and_check(current_frames, current_duration, output_gif)

    logger.info(f"Saved morphed GIF to {output_gif} (size: {current_size/1024:.1f} KB)")
    return output_gif


@app.route('/camera')
def camera_page():
    return render_template('camera.html')


@app.route('/process_images', methods=['POST'])
def process_images():
    """Process two images for morphing animation."""
    data = request.json
    
    first_image_b64 = data['first_image'].split(',')[1]
    second_image_b64 = data['second_image'].split(',')[1]
    
    # Save the images 
    first_fname = f"first_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    first_image_path = os.path.join(temp_dir, first_fname)
    with open(first_image_path, 'wb') as f:
        f.write(base64.b64decode(first_image_b64))
    second_fname = f"second_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    second_image_path = os.path.join(temp_dir, second_fname)
    with open(second_image_path, 'wb') as f:
        f.write(base64.b64decode(second_image_b64))
    
    logger.info(f"Saved two images for morphing: {first_image_path} and {second_image_path}")
    
    try:
        emotions = detect_emotions(second_image_path)
        if not emotions:
            return jsonify(error="No face detected in second image. Please ensure good lighting."), 400
        
        dominant_emotion = emotions
        
        # Create morphing animation
        try:
            gif_path = animate_expression(first_image_path, second_image_path)
        except Exception as e:
            logger.error(f"Error in morphing: {str(e)}")
        
        return jsonify({
            'dominant_emotion': dominant_emotion,
            'gif_path': gif_path
        })
    
    except Exception as e:
        logger.error(f"Failed to process images: {str(e)}")
        return jsonify({'error': f"Failed to process images: {str(e)}"}), 500


@app.route('/download')
def download():
    path = request.args.get('gif_path', '')
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, mimetype='image/gif')


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=ssl_context)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)