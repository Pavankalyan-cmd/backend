from mongoengine import Document, StringField, DecimalField, DateTimeField, DateField,ReferenceField
import datetime
import uuid

def generate_unique_id():
    return str(uuid.uuid4())

class User(Document):
    Id = StringField(primary_key=True, max_length=200)
    Displayname = StringField(required=True)
    email = StringField(required=True)
    photoURL = StringField(required=False)
    CreatedAt = DateTimeField(default=datetime.datetime.utcnow)




class Expense(Document):
    Id = StringField(primary_key=True, default=generate_unique_id, max_length=200) 
    User = ReferenceField(User,required=True)
    Title = StringField(max_length=200, required=True)
    Amount = DecimalField(precision=2, required=True)  # Use precision
    Description = StringField(max_length=400, required=False,blank=True,null=True)
    Tag = StringField(max_length=200, required=True)
    Type = StringField(max_length=200, required=True)
    Paymentmethod = StringField(max_length=200, required=False,blank=True,null=True)
    Date = DateField( required=True)

class Income(Document):
    Id = StringField(primary_key=True, default=generate_unique_id, max_length=200)
    User = ReferenceField(User,required=True)
    Title = StringField(max_length=200, required=True)
    Amount = DecimalField(precision=2, required=True)  # Use precision
    Tag = StringField(max_length=200, required=True)
    Type = StringField(max_length=200, required=True)
    Date = DateField( required=True)
