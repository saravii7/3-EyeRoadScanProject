import time, glob, numpy as np, torch
from PIL import Image
from ultralytics import YOLO
torch.set_num_threads(2)
m = YOLO('run17_best_finetuned.pt')
imgs = [np.array(Image.open(p).convert('RGB')) for p in glob.glob('assets/*.png')+glob.glob('results/run17/*.png')]
rng=np.random.default_rng(42)
imgs += [rng.integers(0,255,(1080,1920,3),dtype=np.uint8) for _ in range(5)]
print(len(imgs),'images')
for sz in (640, 960):
    for im in imgs[:3]: m.predict(im, imgsz=sz, conf=0.46, iou=0.7, max_det=300, device='cpu', verbose=False)
    ts=[]
    for _ in range(2):
        for im in imgs:
            t=time.perf_counter(); m.predict(im, imgsz=sz, conf=0.46, iou=0.7, max_det=300, device='cpu', verbose=False); ts.append(time.perf_counter()-t)
    print(sz, 'median %.3f s  p95 %.3f s  n=%d' % (np.median(ts), np.percentile(ts,95), len(ts)))
