import gerber
from gerber.render import GerberCairoContext

# Read gerber and Excellon files
dim = gerber.read('tty.dim')

# Rendering context
ctx = GerberCairoContext()

# Create SVG image
ctx.color = (0, 1, 0)
dim.render(ctx, "tty_dim.svg")
print(ctx)

ctx.dump("foo.svg")
