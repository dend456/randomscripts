import math, operator, random
from PIL import Image, ImageChops

height = 512
width = 512 * 3

img = Image.new('RGB',(width,height),'black')
newPixels = img.load()

points = []
for i in range(0,25):
    x = random.randint(5,(width//3)-6)
    y = random.randint(5,height-6)
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)

    points.append((x,y,r,g,b))


def getClosestMan(x,y):
    minDist = 999999
    closestPoint = None
    for p in points:
        dist = abs(x - p[0])
        dist += abs(y - p[1])
        if dist < minDist:
            minDist = dist
            closestPoint = p

    return closestPoint

def getClosestEuc(x,y):
    minDist = 999999
    closestPoint = None
    for p in points:
        dist = (x - p[0]) * (x - p[0]) + (y - p[1]) * (y - p[1])
        if dist < minDist:
            minDist = dist
            closestPoint = p

    return closestPoint

def getClosestCheb(x,y):
    minDist = 999999
    closestPoint = None
    for p in points:
        dist = max(abs(x-p[0]),abs(y-p[1]))
        if dist < minDist:
            minDist = dist
            closestPoint = p

    return closestPoint

for y in range(height):
    print(y)
    for x in range(width//3):
        p = getClosestEuc(x,y)
        newPixels[x,y] = (p[2],p[3],p[4])

for y in range(height):
    print(y)
    for x in range(width//3):
        p = getClosestMan(x,y)
        newPixels[x+(width//3),y] = (p[2],p[3],p[4])
        
for y in range(height):
    print(y)
    for x in range(width//3):
        p = getClosestCheb(x,y)
        newPixels[x+(width//3*2),y] = (p[2],p[3],p[4])
        
for p in points:
    for x in range(p[0]-3,p[0]+3):
        for y in range(p[1]-3,p[1]+3):
            newPixels[x,y] = (0,0,0)
            newPixels[x+(width//3),y] = (0,0,0)
            newPixels[x+(width//3*2),y] = (0,0,0)

img.save("a.png")
