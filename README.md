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
or if it is elsewhere.

Searches can combine a number of search criteria and results are presented paginated.

## Installation and setup

You need a (possibly local) web server to run the Flask application in, whose installation and configuration
is not covered here (wsgi, gunicorn, stuff like that).

For the application proper, you need Python3 and the requirements in `requirements.txt`.

As of now it is STILL IN DEVELOPMENT MODE (e.g. all static files are served by the app itself,
the secret key is fake, etc).

To generate the DB, meddle with the `db_testvalues.py` contents and run the `db_generate.py` script.

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

> Develop this into an import/export feature of the app?

If authors or books are inserted (or edited) with name (or title) very **similar to
existing ones**, a warning is raised and the user is asked to confirm her intentions
before completing the insertion (this behaviour can be configured away on a per-user basis).
At the moment *no duplicates are allowed* (in the exact sense) as far as authors are concerned, while for 
books this requirement is relaxed, relying on the sole similarity-warnings (think for example of two
copies of the same books with the same title but in two languages).

**User settings** page to customize interface.

## Major/Future TODOs

MultiHousees
> **MultiHouses**: a single db dealing with multiple users and multiple houses. Each book is `registered` to
> a single house, each user is attached to _her_ house. When editing, she can edit everything
> but gets a warning when touching somebody else's stuff. Books she inserts can only belong to her house.
> User house is set in the settings page. Still, this does not interfere with the `in-house` settings.

RewriteEdits
> The whole handling of the edit endpoints is very cumbersome and bears
> some code duplication. Consider rewriting the whole of it (also
> including the confirm-checkbox) with more reuse!

BetterConversions
> Also make the request-to-arguments and form-to-request conversions more uniform
> and streamlined.

Similarity
> Outsource the similar-thing issue completely to a separate module,
> and perhaps implement digram vector space for more sensible behaviour.

Deploy
> Deploy on a real server (apache, nginx, lighty, etc)

AddreplaceAutomate
> in the two `addreplace` calls, when updating: the list of attributes must be cleverly handled instead
> of doing, as is done now, a lot of explicit member copies.

CancelEscape
> set the no and cancel buttons so that they respond to Esc as the Enter key activates the Save/Yes.

MoreStats
> More advanced statistics (all transactionally handled) in the logged users' homepage.
> E.g. book breakdown per genre, or percentage and number of books that are out

SimilaritySlider
> The threshold for author/book similarity can become a slider one day.

BetterGoBackTo
> e.g. if user goes to book-edit from the author-view page, where to lead it back to? (both on save and cancel)

DisabledEdits
> For users who have canedit=False, all fields are disabled (so that the `edit` windows become cards to inspect)

## Cleanups to do

* all urls in template html's must be built with `url_for`

* The `remember_me` checkbox: either it disappears or it gets implemented (how exactly?).

## Currently doing:

Multihouses:
* there exists a table Houses (id, name, description) **DONE**
* an endpoint/tablepage with Houses **DONE**
* each user has a House and can change it **DONE**
* each user has a 'default searches are limited to my house' setting **DONE**
* books have a 'house' field:
    * database, DONE
    * creation/edit in dbtools DONE
    * import DONE
    * search, DONE
    * listing, DONE
    * addnew/edit DONE
* New books can be created only as sitting in the user's house **DONE**
* Existing books can be relocated only if from user's house **DONE**
* All searches are possible; whether by default the search is only-my-house or all-houses is configurable **DONE**
* There are house-specific book counters, updated transactionally **DONE**
