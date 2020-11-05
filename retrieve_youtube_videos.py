
"""YouTube Videos Retriever

This script allows the user to enter a YouTube channel ID, and retreive a .csv file containing video titles for each
playlist.

This script requires that 'Numpy', 'Pandas', and apiclient.discovery's `build`, are installed within the Python
environment you are running this script in.

This file can also be imported as a module and contains the following functions:

    * get_playlists – returns all of the playlist names contained in a given YouTube channel
    * get_videos – returns all of the videos names contained in a given playlist
    * main – the main function of the script (which allows user interaction)

"""

import numpy as np
import pandas as pd
from apiclient.discovery import build

def main():
    
    """ Allows the user to interact with the program in order to retrieve the videos.
    
    Arguments:
    None

    Returns:
    df (pd.DataFrame): a DataFrame giving of the video names and playlist names, for all of the playlists, 
    for a given channel
    
    """
    
    user_input = ''
    
    # Prompt user to enter API key
    while user_input.lower() not in {'yes', 'y'}:
        
        user_input = input('Do you have a YouTube API key? [yes/no]')
        
        if user_input.lower() in {'n', 'no'}:
            print('\n You will need to get an API key. This is a very quick process. \
            \n\n Please follow the instructions here: \
            \n https://developers.google.com/youtube/registering_an_application')
    
    global youtube
    youtube = None
    
    while youtube == None:
        user_input = input('Pleade enter your API key:')
        
        # Construct a Resource object for interacting with YouTube's API
        try: 
            youtube = build('youtube', 'v3', developerKey = user_input)
        
        except:
            print('Key invalid.')
    
    user_input = True
    
    # Prompt user to enter Channel ID
    while user_input:
        user_input = input('Please enter your Channel ID. This can be found by signing in to YouTube and looking at URL of the \'Your channel\' page. It can also be found by clicking on \'Advanced settings\'. \n\n')
    
        # Run custom get_playlists() function to get playlists for given Channel ID
        try:
            df_playlists = get_playlists(user_input)
            print('\nDownloading videos...')
            global channel_id
            channel_id = user_input
            user_input = False
            
        except:
            print('Channel ID invalid.')
    
    # Run custom function to get videos for each playlist
    video_data = [get_videos(i) for i in df_playlists['Playlist ID']]
    
    # Concatenate each dataframe containing videos for each playlist
    df = pd.concat(video_data)
    
    # Sort alphabetically by playist name, but preserve order of videos within each playlist
    df = df.rename_axis('Index').sort_values(by = ['Playlist Name', 'Index'], ascending = [True, True])
    
    # Clean final table (drop any duplicates retreived, reset index)
    df = df.drop_duplicates().reset_index(inplace = False)
    df.drop(columns = ['Index'], inplace = True)
    df.reset_index(inplace = True, drop = True)
    
    print(df)
    
    print('\nDownload complete!')
    
    # Allow user to donwload the .csv file
    user_input = input('Would you like to download the result as a .csv file? [yes/no]')
    
    if user_input.lower() in {'y', 'yes'}:
        df.to_csv("./my_youtube_videos.csv", index = False)
        print('File downloaded!')
    
    return df

def get_playlists(channel_id):
    
    """ Returns all of the playlist names contained in a given YouTube channel.
    
    Arguments:
    channel_id (str): characters that uniqiely identify a given channel

    Returns:
    df (pd.DataFrame): a DataFrame giving the playlist name and playlist_id for each playlist
    
    """

    # Request data from API for given Channel ID
    channel_request = youtube.playlists().list(part = 'snippet', channelId = channel_id).execute()
    
    next_page_token = channel_request.get('nextPageToken')
    
    # Logic to cycle through pages using nextPageToken
    while 'nextPageToken' in channel_request:
    
        next_page = youtube.playlists()\
        .list(part = 'snippet',channelId = channel_id, pageToken = next_page_token).execute()
    
        channel_request['items']  += next_page['items']
    
        if 'nextPageToken' not in next_page:
            channel_request.pop('nextPageToken')
        
        else:
            next_page_token = next_page['nextPageToken']
    
    # Get video titles from snippet
    playlists = [i['snippet']['title'] for i in channel_request.get('items')]
    
    # Get Playlist IDs
    playlist_ids = [i['id'] for i in channel_request.get('items')]
    
    df = pd.DataFrame({'Playlist Name':pd.Series(playlists), 'Playlist ID': pd.Series(playlist_ids)})
    
    return df

def get_videos(playlist_id):
    
    """ Returns all of the videos names contained in a given playlist.
    
    Arguments:
    playlist_id (str): characters that uniqiely identify a given playlist

    Returns:
    df (pd.DataFrame): a DataFrame giving the video name and playlist name for each video
    
    """
    
    # Request data from API for given Playlist ID
    playlist_request = youtube.playlistItems().list(part = 'snippet', playlistId = playlist_id).execute()
    
    next_page_token = None
    
    # Logic to cycle through pages using nextPageToken
    while 'nextPageToken' in playlist_request:
    
        next_page = youtube.playlistItems()\
        .list(part = 'snippet', playlistId = playlist_id, pageToken = next_page_token ).execute()
    
        playlist_request['items']  += next_page['items']
    
        if 'nextPageToken' not in next_page:
            playlist_request.pop('nextPageToken')
        
        else:
            next_page_token = next_page['nextPageToken']
    
    # Get video titles from snippet
    videos = [i['snippet']['title'] for i in playlist_request.get('items')] 
    
    # Get playlist name for given playlist_id, using the custom get_playlists() function
    playlist_col = get_playlists(channel_id)
    playlist_col = playlist_col[playlist_col['Playlist ID'] == playlist_id]['Playlist Name']
    playlist_col= playlist_col.values[0]
    
    # Create df for videos, and set every value of playlist Name as the same
    df = pd.DataFrame({'Playlist Name':playlist_col, 'Video Title':pd.Series(videos, dtype = str)})
    
    return df

if __name__ == '__main__':
    main()
