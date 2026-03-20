# Assets for the Windows Installer

Place the following files here for the Inno Setup installer:

- `icon.ico` — Application icon (256x256 recommended, multi-size .ico)
- `wizard.bmp` — Installer sidebar image (164x314 pixels)
- `wizard_small.bmp` — Installer header image (55x55 pixels)

## Quick icon generation

If you don't have an .ico file yet, you can create one from a PNG:

```powershell
# Using ImageMagick (install via: winget install ImageMagick)
magick convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

Or use any online PNG-to-ICO converter.
