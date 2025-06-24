from ultralytics import YOLO, checks, hub
checks()

hub.login('a004630660b1c3aa538c30c9fa74294af446b87170')

model = YOLO('https://hub.ultralytics.com/models/JFfH1i8oGolYMkrGEYAN')
results = model.train()
