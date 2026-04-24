import random
import math

def lerp(a, b, x):
    """Linear interpolation between a and b by x amount"""
    return a + x * (b - a)

def fade(t):
    """Fade function for Perlin noise"""
    return t * t * t * (t * (t * 6 - 15) + 10)

def gradient(h, x, y):
    """Compute the dot product for the gradient"""
    vectors = [
        (1, 1), (-1, 1), (1, -1), (-1, -1),
        (1, 0), (-1, 0), (0, 1), (0, -1)
    ]
    g = vectors[h % 8]
    return g[0] * x + g[1] * y

def simple_noise2d(x, y, seed=0):
    """Simple 2D noise implementation"""
    # Set up grid
    x0 = math.floor(x)
    y0 = math.floor(y)
    x1 = x0 + 1
    y1 = y0 + 1
    
    # Get fractional part
    dx = x - x0
    dy = y - y0
    
    # Smoothing
    u = fade(dx)
    v = fade(dy)
    
    # Hash coordinates of the 4 corners
    random.seed(seed)
    p = [random.randint(0, 255) for _ in range(512)]
    
    aa = p[(p[int(x0) % 256] + int(y0)) % 256]
    ab = p[(p[int(x0) % 256] + int(y1)) % 256]
    ba = p[(p[int(x1) % 256] + int(y0)) % 256]
    bb = p[(p[int(x1) % 256] + int(y1)) % 256]
    
    # Interpolate
    x1 = lerp(gradient(aa, dx, dy), gradient(ba, dx-1, dy), u)
    x2 = lerp(gradient(ab, dx, dy-1), gradient(bb, dx-1, dy-1), u)
    return lerp(x1, x2, v)

def pnoise2(x, y, octaves=6, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024, base=0):
    """Fallback implementation of Perlin noise with octaves"""
    total = 0
    frequency = 1
    amplitude = 1
    max_value = 0
    
    for i in range(octaves):
        total += simple_noise2d(x * frequency, y * frequency, base + i) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= lacunarity
    
    return total / max_value
