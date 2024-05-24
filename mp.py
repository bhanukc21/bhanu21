from flask import Flask, render_template, request
from flask import send_from_directory
from flask import Flask, render_template, request, session, redirect, url_for
import numpy as np
import pickle
from datetime import datetime
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
from sklearn.decomposition import PCA
import csv
import os
import pandas as pd

app = Flask(__name__)
secret_key = os.urandom(24)
app.secret_key = secret_key

# Load saved or trained models
with open('kmeans_model.pkl', 'rb') as f:
    kmeans = pickle.load(f)

with open('pca_model.pkl', 'rb') as f:
    pca = pickle.load(f)

# Define manual cluster labels
manual_cluster_labels = {
    0: 'Education',
    1: 'Business',
    2: 'cinema',
    3: 'sports',
    4: 'crime'
}
def read_csv_data():
    data = {}
    with open('TrendingPosts.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            category = row['Predicted_Cluster_Label']
            if category not in data:
                data[category] = []
            data[category].append({'title': row['Text']})
    return data

# Function to append user input and predicted cluster to CSV file
def append_to_csv(user_input, predicted_cluster):
    try:
        # Get the current date
        current_date = datetime.now().strftime("%d-%m-%Y")
        

        # Get the absolute path to the CSV file 
        with open('TrendingPosts.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            # Write user input, predicted cluster, social media name, and date of adding the post to CSV
            writer.writerow(['Instagram', current_date, user_input,predicted_cluster])
        return True  # Return True if writing to CSV was successful
    except Exception as e:
        print("Error:", e)
        return False
        
 
# Home route
@app.route('/')
def home():
    username = session.get('username')
    if username:
        return render_template('home.html', username=username)
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

def write_to_csv(data):
    with open('users.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open('users.csv', mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username and row[3] == password:
                    session['username'] = username
                    return redirect(url_for('profile'))
        error = 'Invalid username or password.'
        return render_template('login.html', error=error)
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'username' in session:
        return redirect(url_for('home'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None  # Initialize error message variable
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        terms = request.form.get('terms')
        
        if password != confirm_password:
            return 'Passwords do not match'
        
        # Check if username or email already exists in CSV file
        with open('users.csv', mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username or row[1] == email:
                    error = 'User already exists'
                    break  # Exit loop once user is found
            
            if error is None:  # If no error, write registration data to CSV file
                write_to_csv([username, email, phone, password])
                # Redirect to login page after successful registration
                return redirect(url_for('login_form'))
    
    return render_template('registration.html', error=error)  # Pass error to template


@app.route('/index')
def index():
    if 'username' in session:
        return render_template('index.html')
    else:
        return render_template('login.html')
        

@app.route("/category/<category>")
def category(category):
    return render_template("sports.html", category=category)

@app.route("/posts/<category>")
def posts(category):
    data = read_csv_data()
    posts = data.get(category, [])[:5]  # Get top 5 posts for the selected category
    return render_template("top_posts.html", category=category, posts=posts)

@app.route('/TrendingPosts.csv')
def get_cluster_results():
    return send_from_directory( 'TrendingPosts.csv', as_attachment=True)





# Load the CSV file containing the sentences
data = pd.read_csv("TrendingPosts.csv", encoding='latin-1')

# Generate visualizations
# Count occurrences of each social media platform
social_media_counts = data['SOCIAL MEDIA'].value_counts().reset_index()
social_media_counts.columns = ['Social Media Platform', 'Number of Posts']

# Create pie chart
fig_pie = px.pie(social_media_counts, values='Number of Posts', names='Social Media Platform',
                 title='Distribution of Posts by Social Media Platform')

# Group data by date and predicted cluster label and count the number of posts
date_cluster_counts = data.groupby(['DATE', 'Predicted_Cluster_Label']).size().reset_index(name='Number of Posts')

# Create stacked bar chart
fig_stacked_bar = px.bar(date_cluster_counts, x='DATE', y='Number of Posts', color='Predicted_Cluster_Label',
                         title='Distribution of Predicted Clusters Over Time',
                         labels={'DATE': 'Date', 'Number of Posts': 'Number of Posts', 'Predicted_Cluster_Label': 'Predicted Cluster Label'},
                         barmode='stack')

# Create line graph
fig_line_graph = px.line(date_cluster_counts, x='DATE', y='Number of Posts', color='Predicted_Cluster_Label',
                         title='Distribution of Predicted Clusters Over Time',
                         labels={'DATE': 'Date', 'Number of Posts': 'Number of Posts', 'Predicted_Cluster_Label': 'Predicted Cluster Label'})

# Group data by predicted cluster label and social media platform
cluster_social_media_counts = data.groupby(['Predicted_Cluster_Label', 'SOCIAL MEDIA']).size().reset_index(name='count')

# Create grouped bar chart
fig_grouped_bar = px.bar(cluster_social_media_counts, x='Predicted_Cluster_Label', y='count', color='SOCIAL MEDIA',
                         barmode='group',
                         title='Distribution of Posts by Predicted Cluster and Social Media Platform',
                         labels={'Predicted_Cluster_Label': 'Predicted Cluster Label', 'count': 'Number of Posts', 'SOCIAL MEDIA': 'Social Media Platform'})




@app.route('/visualizations')
def display_visualizations():
    return render_template('visualizations.html',
                           pie_chart=fig_pie.to_html(full_html=False),
                           stacked_bar_chart=fig_stacked_bar.to_html(full_html=False),
                           line_graph=fig_line_graph.to_html(full_html=False),
                           grouped_bar_chart=fig_grouped_bar.to_html(full_html=False))

with open('DBSCAN.pkl', 'rb') as f:
    DBSCAN_MODEL = pickle.load(f)


# Prediction route
@app.route('/predict', methods=['POST'])
def predict():
    user_input = request.form['user_input']
    # List of cluster labels
    cluster_labels = ['cinema', 'crime', 'sports', 'business/economy', 'education/tech']
    # Get the label
    predicted_label = DBSCAN_MODEL(user_input,cluster_labels)["labels"][0]
    # Append user input and predicted cluster to CSV file
    append_to_csv(user_input, predicted_label )
    return render_template('predict.html', user_input=user_input, predicted_label=predicted_label)


if __name__ == '__main__':
    app.run(debug=True,port=5500)



# cluster_labels = ['cinema', 'crime', 'sports', 'business/economy', 'education/tech']
# # Perform prediction
# predicted_sentences = []

# # Iterate through sentences
# for sentence in new_sentences:
#     # Get the label
#     predicted_label = DBSCAN_MODEL(sentence, cluster_labels)["labels"][0]
#     predicted_sentences.append((sentence, predicted_label))
# # Create DataFrame
# df = pd.DataFrame(predicted_sentences, columns=['POST', 'Predicted Label'])
# # Display DataFrame
# print(df)