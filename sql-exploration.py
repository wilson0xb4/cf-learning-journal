# coding: utf-8
foo = 'bar'
foo
from journal import DATABASE_URL
DATABASE_URL
get_ipython().magic(u'ls ')
from sqlalchemy import create_engine
engine = create_engine(bind=DATABASE_URL)
engine = create_engine(DATABASE_URL)
engine = create_engine(DATABASE_URL, echo=True)
engine
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()
session
session.bind
from journal import Entry
from __future__ import unicode_literals
e1 = Entry()
e1.title = "There's Something About SQLAlchemy"
e1.text = "It's such a wonderful system for interacting with a database!"
el
e1
session.new
session.dirty
session.add(e1)
session.new
session.dirty
session.commit()
results = session.query(Entry)
results
dir(results)
str(results)
results = results.all()
results
type(results)
for e in results:
    print(entry.title)
    print("\t{}".format(entry.text))
    
for e in results:
    print(e.title)
    print("\t{}".format(e.text))
    
results = session.query(Entry).order_by(Entry.title).all()
for e in results:
    print(e.title)
    print("\t{}".format(e.text))
    
for e in results:
    print("{}: {}".format(e.id, e.title))
    print("\t{}".format(e.text))
    
results = session.query(Entry).order_by(Entry.created).all()
for e in results:
    print("{}: {}".format(e.id, e.title))
    print("\t{}".format(e.text))
    
results = session.query(Entry).order_by(Entry.created.desc()).all()
for e in results:
    print("{}: {}".format(e.id, e.title))
    print("\t{}".format(e.text))
    
results = session.query(Entry).order_by(Entry.created.desc())
results.count()
results.session.query(Entry).get(2)
results !
results = results.session.query(Entry).get(2)
results.id
results.title
results = results.session.query(Entry).get(5)
results = session.query(Entry).get(5)
results = session.query(Entry)
results.one()
results = session.query(Entry)
results
results = results.filter(Entry.id==2)
results
str(results)
results.one()
my_entry = _
my_entry
my_entry.title
my_entry.title = "It's time for number two!"
session.dirty
session.new
session.commit()
get_ipython().magic(u'save sql-exploration.py 1-69')
