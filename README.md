# Embroidery Thread Palette Converter

> A Python script to pull threads from https://embroiderynerd.io and generate Adobe Illustrator/Photoshop Color Swatches

This script was built to automate the task of creating Adobe Swatch Exchange (.ase) files for several hundered embroidery thread brands and manufactures. It pulls from the online database hosted, by The Embroidery Nerds, to ensure that it is the most extensive library of ASE files.

_Disclaimer: The swatch files may contain names that are registered trademarks or copyrighted material owned by their respective owners. The use of such names is for descriptive purposes only. All rights to these names are owned by their respective owners._

| Adobe Illustrator                       | CorelDraw GS 2023                       |
| --------------------------------------- | --------------------------------------- |
| ![img](https://i.imgur.com/63P07nW.png) | ![img](https://i.imgur.com/kwMnr95.png) |

## 🎨 Features

- Pull data from over 35k threads instantly
- Generate Adobe Swatch Exchange files containing colors with the thread spool label right on the swatch
- CorelDraw support has been added

## 🐾 How to Install/Use the Swatches

Download the [repo's files](https://github.com/Matthewenderle/ThreadChart-to-Adobe-Swatch/archive/refs/heads/main.zip) from this repository and extract the zip archive. You'll see two folders called `adobe-swatches` and `corel-swatches`. Those folders have the relevant files needed for importing. Then follow the applicable section.

#### Adobe Illustrator

To import all the thread charts, create a folder called _Thread Charts_ in `C:\Program Files\Adobe\Adobe Illustrator CS6 (64 Bit)\Presets\en_US\Swatches\` and copy all the swatches there. You can remove charts you don't need or want to make the list shorter.

Alternatively, with Adobe Illustrator open, you may click on the lower left icon in the _Swatches Panel_ to select from installed swatches, and open the _thread_chart.ase_ file that you'd like to import.

#### CorelDraw

To import all the thread charts, create a folder called _Thread Charts_ in `C:\Program Files\Corel\CorelDRAW Graphics Suite 2022\Color\Palettes` and copy all the swatches there. You can remove charts you don't need or want to make the list shorter.

## Download premade Swatch Files

You can find all the latest Adobe Swatch files in the [_adobe-swatches_](https://github.com/Matthewenderle/ThreadChart-to-Adobe-Swatch/tree/main/adobe-swatches) folder above. Check out the date next to the files there to see the last time it was updated.

Please be aware that Adobe _.ase_ files are not openable in a text editing program. They are binary files that can only be ran in Adobe products.

*CorelDraw files are available under [*corel-swatches*](https://github.com/Matthewenderle/ThreadChart-to-Adobe-Swatch/tree/main/corel-swatches) folder*.

### Loading a Swatch Library into Adobe Illustrator

![loading-file](https://i.imgur.com/3fMWKZY.gif)

### Loading a Swatch Library into CorelDraw

![loading-file-coreldraw](https://imgur.com/98RQZn6.gif)

## Want to run it yourself?

Clone it to local computer. Install python libraries.

_Please Note:_ You will need to request access to the ThreadConverter database. Create an issue to request access.

```sh
$ git clone https://github.com/Matthewenderle/ThreadChart-to-Adobe-Swatch.git
$ pip install psycopg2
# rename sample.config.ini to config.ini and enter the database connection details
$ python main.py
# or to generate CorelDraw files
$ python coreldraw.py
```

## 📦 Python Libraries

### psycopg2

| Name                                              | Description                                        |
| ------------------------------------------------- | -------------------------------------------------- |
| [`psycopg2`](https://github.com/psycopg/psycopg2) | required to connect to the database and pull data. |
