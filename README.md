# FlaskBiblio

A simple Flask application to manage my parents' library.

## Basic description

Users operate on a database of books and authors via a web application. Mainly:
* add
* edit
* remove
* search

on books and authors. Books can have zero, one or more authors (relations are enforced upon author deletion).

Books have a _in-house_ attribute, marking whether the book is in its rightful location
or if it is elsewhere. Also, the system includes several "houses", representing different
libraries.

Searches can combine a number of search criteria and results are presented paginated.

## Installation and setup

You need a (possibly local) web server to run the Flask application in, whose installation and configuration
is not covered here (wsgi, gunicorn, stuff like that).

For the application proper, you need Python3 and the requirements in `requirements.txt`.

As of now it is STILL IN DEVELOPMENT MODE (e.g. all static files are served by the app itself,
the secret key is fake, etc).

To generate the DB, meddle with the `db_testvalues.py` contents and run the `db_generate.py` script.
Additionally, to import a `csv` file, see the remars on the import procedure below.

## Technical specifications

* The DB is a simple sqlite local database.
* Uses bootstrap (via flask-bootstrap) with some font-awesome for the frontend.
* Uses flask and wtforms to build and serve pages and query the DB.
* No javascript is written here: everything (with some ugly acrobatics) is done through static forms and static pages.

## Notable features

Search results (including, as a special case thereof, the listing of _all_ results)
are **paginated**. The DB however is queried for full results on every page request (which _may not_ scale
well for large libraries). To implement the return-to-prev-page on hitting Cancel buttons, the last query
is stored in Flask's `session` object.

> Consider whether to handle differently the pagination issue (which does not scale well like it is).

> Also the request args are stored as a dict for the return-from-cancel, hence possible multidict issues are lost. To fix.

There is a nice **import script** to import from a formatted `csv` file: it proceeds in three steps, guiding
the user through some of the inconsistencies and warning involved.

If authors or books are inserted (or edited) with name (or title) very **similar to
existing ones**, a warning is raised and the user is asked to confirm her intentions
before completing the insertion (this behaviour can be configured away on a per-user basis).
At the moment *no duplicates are allowed* (in the exact sense) as far as authors are concerned, while for 
books this requirement is relaxed, relying on the sole similarity-warnings (think for example of two
copies of the same books with the same title but in two languages).
It works on a digram basis of letters-only, but can be reconfigured (in the `config.py`) to fall
back to single-letter vector space.

**User settings** page to customize interface.

**MultiHouses**: a single db dealing with multiple users and multiple houses. Each book is "registered" to
a single house, each user is attached to _her_ house. When editing, she can edit only her stuff.
Books she inserts can only belong to her house.
User house is set in the settings page. Still, this does not interfere with the _in-house_ settings.
Note that one can still edit and work on other houses, but this is made deliberately difficult, so that
one has to know what she is doing. By temporarily changing her house in the settings, the user can access other houses' stuff.  
* there exists a table Houses (id, name, description)
* an endpoint/tablepage with Houses
* each user has a House and can change it
* each user has a 'default searches are limited to my house' setting
* books have a 'house' field:
    * database,
    * creation/edit in dbtools
    * import
    * search,
    * listing,
    * addnew/edit
* New books can be created only as sitting in the user's house
* Existing books can be relocated only if from user's house
* All searches are possible; whether by default the search is only-my-house or all-houses is configurable
* There are house-specific book counters, updated transactionally

**DisabledEdits**
When user cannot edit the book (canedit=False or the book belong to a foreign house),
the edit-book view has disabled fields: text-boxes ('readonly' html attribute),
checkboxes and lists ('disabled' attribute) and - most cumbersome - the multi-checkbox
representing the languages. To address the latter, a custom render chain is implemented
in MultiCheckboxField.py which passes down the 'disabled' attribute from the container
multi-checkbox widgets down to the individual checkbox html code.

**Deploy**
* With lighttpd **DONE**:
    * the biblio.db file must be writable by the right user (www-data for lighty) or read-only-error
        would be raised upon DB write operations.
    * sample conf file for lighttpd, see docs directory
> To do for apache with htaccess

**BookStats** are handled in an unified manner, through functions that make each book/author/...
into a vector of counters. Those are applied algebraically and displayed in a sorted-grouped manner on the
index page.

## Major/Future TODOs

StructuredImport
> Split the erase-books-and-authors and the import-stuff functions and think carefully
> about the authorlist phase, so that several lists of books can be imported
> sequentially, possibly belonging to different houses.
> **Later**, make this an import/export feature of the app?

RewriteEdits
> The whole handling of the edit endpoints is very cumbersome and bears
> some code duplication. Consider rewriting the whole of it (also
> including the confirm-checkbox) with more reuse!

BetterConversions
> Also make the request-to-arguments and form-to-request conversions more uniform
> and streamlined.

AddreplaceAutomate
> in the two `addreplace` calls, when updating: the list of attributes must be cleverly handled instead
> of doing, as is done now, a lot of explicit member copies.

SimilaritySlider
> The threshold for author/book similarity can become a slider one day.

## Cleanups to do

* The `remember_me` checkbox: either it disappears or it gets implemented (how exactly?).

## Currently doing:
