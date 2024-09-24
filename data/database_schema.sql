-- SQL script to define the database schema

-- Create table for storing video details
CREATE TABLE IF NOT EXISTS video_details (
    video_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    upload_date TEXT,
    duration INTEGER,
    channel_name TEXT
);

-- Create table for storing transcript data
CREATE TABLE IF NOT EXISTS transcripts (
    video_id TEXT PRIMARY KEY,
    transcript TEXT NOT NULL,
    FOREIGN KEY (video_id) REFERENCES video_details (video_id)
);

-- Add necessary indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_video_details_upload_date ON video_details (upload_date);
CREATE INDEX IF NOT EXISTS idx_transcripts_video_id ON transcripts (video_id);
