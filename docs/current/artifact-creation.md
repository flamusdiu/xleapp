# Creating Artifacts

This is a completely new way to add artifacts to xLEAPP application from iLEAPP, RLEAPP, and related applications.

* [Basic Information](#basic-info)
* [Skeleton Artifact](#skeleton)
* [Saving Report Data](#saving-report-data)
* [Publishing Artifacts](#publishing-artifacts)

<h2 id="basic-info">Basic Information</h2>

Below, I have layed out a basic artifact pulling a SQLite database. Things to remember:

* "MyArtifact" must be unique for each artifact. This should be descriptive name for the artifact.
* `__post__init__()` functions contains several metadata fields for the artifact. Here is the complete list of these fields:
  * description - information of the artifact shown on the HTML report
  * name - Name of the artifact shown on the HTML report
  * category - Category where the artifact is listed on the HTML report
  * kml - Artifact saves KML data
  * report - Produce HTML report. Setting this to "False" forces NO report to be generated
  * report_headers - Headers for the HTML tables in the HTML report. This can be a list of tuples where each tuple if a different table. If not present, then `('Key', 'Value')` tuple is used.
  * timeline - Artifact saves timeline data
  * web_icon - Icon from Feathers.JS icons for the HTML Report. Check `xleapp/report/_webicons.py` for a list of icons.
* There are also two decorators you can use to mark an artifact. These are not used very often.
  * core_artifact: marks an artifact as `core` artifact. These artifacts are run first and ALWAYS ran.
    * mark as following:

        ```python
        @core_artifact
        class MyArtifact(Artifact):
            pass
        ```

  * long_running_process: these artifacts must be selected manually.
    * mark as following:

        ```python
        @long_running_process
        class MyArtifact(Artifact):
            pass
        ```

Searching is the core of processing any artifact. To process files for your artifacts, you add the `@Search()` decorator to your `process()` function. You add a list within the decorator as shown below. The files are automatically opened for you if there are less then **10** files. These are returned to the artifact through the `self.found` attribute of the artifact.

There are two other options usable with this decorator:

* file_names_only
* return_on_first_hit

First, `file_names_only` returns a list of file paths to your artifact instead of open files mimicking the way iLEAPP works today. If the search returns more then **10** files, then you automatically get a list of file paths.

Second, `return_on_first_hit` ensures that the very first file found is returned.

<h2 id="skeleton">Skeleton Artifact</h2>

```python
from xleapp import Artifact, WebIcon, Search


class MyArtifact(Artifact):
    # This is for SQLite Database Artifacts.
    def __post_init__(self):
        self.name = "Artifact Name"
        self.category = "Applications"
        self.web_icon = WebIcon.GRID
        self.report_headers = ("Column 1", "Column 2", "Column 3")

    @Search("**/database.sqlite")
    def process(self):
        for fp in self.found:
            cursor = fp().cursor()
            # Replace this query with the proper one.
            cursor.execute(
                """
                SELECT column1, column2, column3
                FROM my_table
                """,
            )

            # Everything below here is used to construct the list of information
            # from the artifact.
            #
            # Note: Either syntax works => row['column1'] == row[0]
            all_rows = cursor.fetchall()
            if all_rows:
                for row in all_rows:
                    self.data.append((row['column1'], row['column2'], row['column3']))

```

<h2 id="saving-report-data">Saving Report Data</h2>

`self.data` is where your data found is saved. This is a list containing a table matrix of data. For example:

```python

self.data = [
    [1, 'apple', 'oranges'],
    [2, 'apple', 'oranges'],
    [3, 'apple', 'oranges']
]
```

Translates to:

```html
<table>
<thead>
    <th>Column 1</th>
    <th>Column 2</th>
    <th>Column 3</th>
</thead>
<tbody>
    <tr>
        <td>1</td>
        <td>apple</td>
        <td>oranges</td>
    </tr>
    <tr>
        <td>2</td>
        <td>apple</td>
        <td>oranges</td>
    </tr>
    <tr>
        <td>3</td>
        <td>apple</td>
        <td>oranges</td>
    </tr>
</tbody>
</table>
```

| Column 1 | Column 2 | Column 3 |
| -------- | -------- | -------- |
| 1        | apple    | oranges  |
| 2        | apple    | oranges  |
| 3        | apple    | oranges  |

If you have more then one table of a data, your create your `self.data` like this:

```python
self.data = [
    [ # first table
        [1, 'apple', 'oranges'],
        [2, 'apple', 'oranges'],
        [3, 'apple', 'oranges']
    ],
    [ # second table
        [1, 'apple', 'oranges'],
        [2, 'apple', 'oranges'],
        [3, 'apple', 'oranges']
    ]
]
```

This produces two tables in the report.

The **_recommended_** way save data for the report is:

```python
all_rows = cursor.fetchall()
if all_rows:
    for row in all_rows:
        self.data.append(tuple(row.values()))
```

`tuple(row.values())` expands the row data for the report in the same order as the SQL query. Generally, if you are NOT requiring to modify the table order (which can be done in the SELECT statement) or modifying the column data for the report, then use this method.

For plists or other dictionaries, be careful using this method. Since Python 3.7 ([ref](https://docs.python.org/3.7/library/stdtypes.html#typesmapping)), dictionary are ordered. If you have not created the dictionary to know the insertion order, do not rely on this method!


If you need to construct the tuples for some advance processing, then either below works.

```python
data_list.append((row['column1'], row['column2'], row['column3']))
```

 and

```python
data_list.append((row[0], row[1], row[2]))
```

are equal in output. The first one using column head is the **_preferred_** method to make the artifacts easier to follow.

<h2 id="publishing-artifacts">Publishing Artifacts</h2>

Artifacts need to be published under the proper plugin package.

For ios:

* [xleapp-ios](https://github.com/flamusdiu/xleapp-ios/)
* [xleapp-ios-non-free](https://github.com/flamusdiu/xleapp-ios-non-free)

> Be aware, that `non-free` packages contain artifacts that have licenses not compatible with the MIT license. This also will be missing from binary distributed with Autopsy.

You need to add the plugin to the `xleapp-ios/src/xleapp-ios/plugins` folder. This will be **automatically** picked up by `xleapp` as long a it matches the [Skeleton Artifact](#skeleton) section above.
