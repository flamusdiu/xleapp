HTML report
===========

HTML Report Overview
********************
After processing is complete go to the selected output location. There you will find a folder named in the 
following format:

xLEAPP_Reports_YEAR_MONTH_DAY_DAYOFTHEWEEK_TIME

Sample output folder:

.. thumbnail:: _images/sample_output_folder.png
    :title: Sample output folder

Inside the folder there will be additional folders and HTML files. Even though pressing any of the HTML pages 
will take you to the HTML report the starting point is named index.html.

.. thumbnail:: _images/html_report_starting_page.png
    :title: HTML Report Starting Page Location

The starting index page will look as follows:

.. thumbnail:: _images/html_report_index_page.png
    :title: HTML Report Index (Start) Page Example

Notice the Case Information section in the center. The default tab has general case information. The other tabs 
will give you access to the following:

Device details

.. thumbnail:: _images/html_report_device_details.png
    :title: HTML Report Device Details Section

Script run log

.. thumbnail:: _images/html_report_script_run_log.png
    :title: HTML Report Script Run Log Section

Processed file list

.. thumbnail:: _images/html_report_processed_file_list.png
    :title: HTML Report Processed File List

Notice the left side of the report has all the parsed artifact by category and artifact name. Pressing one of 
the artifact names will show a grip like structure with the artifact output in the center of the report.

.. thumbnail:: _images/html_report_ios_mail_report.png
    :title: HTML Report IOS Mail Report Section


Each artifact has a search bar and the columns can be sorted.

Tab Separated Value Reports
***************************

After processing is completed a collection of tab separated value (TSV) files will be located in the _TSV 
Exports folder inside the generated report directory.

_TSV Exports folder:

.. thumbnail:: _images/tsv_export.png
    :title: _TSV Exports Folder

The first line of each TSV file corresponds to the data headers. All lines below it are the parsed artifact data.

Sample TSV export:

.. thumbnail:: _images/sample_tsv_export.png
    :title: Sample TSV export

TSV exports are suited for ingestion into other tools for further analysis.
