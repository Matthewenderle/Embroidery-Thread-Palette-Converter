# ThreadChart to Adobe Swatch

> A Python script to pull threads from https://threadcharts.com and generate Adobe Illustrator/Photoshop Color Swatches

This script was built to automate the task of creating Adobe Swatch Exchange (.ase) files for several hundered embroidery thread brands and manufactures. It pulls from the online database hosted, by The Embroidery Nerds, to ensure that it is the most extensive library of ASE files.

![img](https://i.imgur.com/63P07nW.png)

## 📦 Python Libraries

### mysql.connector

| Name | Description |
| --- | --- |
| [`mysql.connector`](https://github.com/mysql/mysql-connector-python) | required to connect to the database and pull data.  |


## 🎨 Features

* Pull data from over 35k threads instantly
* Generate Adobe Swatch Exchange files containing colors with the thread spool label right on the swatch

## 🐾 Examples

### Animate logos into GIFs

![loading-file](https://i.imgur.com/3fMWKZY.gif)


## Download premade Swatch Files

You can find all the latest swatch files in the [*swatches folder*](https://github.com/Matthewenderle/ThreadChart-to-Adobe-Swatch/tree/main/swatches) above. Check out the date next to the files there to see the last time it was updated.

Please be aware that Adobe *.ase* files are not openable in a text editing program. They are binary files that can only be ran in Adobe products. 

*CorelDraw files coming soon*.

## Want to run it yourself?

Clone it to local computer. Install python libraries.

```sh
$ git clone https://github.com/Matthewenderle/ThreadChart-to-Adobe-Swatch.git
$ pip install mysql.connector
$ python main.py
```

