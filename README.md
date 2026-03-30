# Drive Organizer - FOR BUSINESSES

Automatically organizes Google Drive files into categorized folders using Claude AI. Scans a Drive folder recursively, sends file names and metadata to Claude for categorization, then moves each file into the appropriate subfolder.

**Categories:** Finance, HR, Projects, Legal, Personal, Other

## How It Works

1. Connects to Google Drive via OAuth2
2. Recursively scans a target folder and all subfolders
3. Sends file names and metadata to Claude API for categorization
4. Creates category subfolders if they don't exist
5. Moves each file into its assigned category folder
6. Logs every action to `organizer.log`

## Prerequisites

- Python 3.9+
- A Google Cloud project with the Drive API enabled
- An Anthropic API key

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/drive-organizer.git
cd drive-organizer
pip install -r requirements.txt
```

### 2. Set up Google Cloud credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or select an existing one)
3. Enable the **Google Drive API** (APIs & Services > Library)
4. Configure the **OAuth consent screen** (APIs & Services > OAuth consent screen)
   - Choose **Internal** if using a Google Workspace account
   - Choose **External** for personal accounts (add your email as a test user)
5. Create **OAuth credentials** (APIs & Services > Credentials > Create Credentials > OAuth client ID)
   - Application type: **Desktop app**
6. Download the JSON file and save it as `credentials.json` in the project folder

### 3. Set environment variables

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Then set them in your shell:

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export DRIVE_FOLDER_ID="your-google-drive-folder-id"
```

The folder ID is the last part of the Google Drive folder URL:
`https://drive.google.com/drive/folders/<THIS_PART>`

Add both exports to your `~/.bash_profile` or `~/.zshrc` to persist them.

### 4. First run

```bash
python3 organizer.py --limit 5
```

On the first run, a browser window will open for Google OAuth login. Select the account that owns the target Drive folder. After authorization, a `token.json` is saved so you won't need to log in again.

The `--limit 5` flag processes only 5 files as a test. Once you're satisfied, run without it:

```bash
python3 organizer.py
```

## Scheduling (macOS)

A launchd plist template is included to run the organizer on a schedule.

1. Copy and edit the template:
   ```bash
   cp com.example.drive-organizer.plist com.yourlabel.drive-organizer.plist
   ```

2. Replace all placeholder values in the plist:
   - `/PATH/TO/drive-organizer` — full path to this project
   - `YOUR_ANTHROPIC_API_KEY` — your Anthropic API key
   - `YOUR_GOOGLE_DRIVE_FOLDER_ID` — your Drive folder ID
   - Adjust `Weekday` (1=Mon, 5=Fri, 7=Sun) and `Hour`/`Minute` as needed

3. Install and load:
   ```bash
   cp com.yourlabel.drive-organizer.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.yourlabel.drive-organizer.plist
   ```

4. To stop:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.yourlabel.drive-organizer.plist
   ```

Your Mac must be awake at the scheduled time. If asleep, launchd runs the job when the Mac next wakes.

## Customization

Edit `config.py` to change:
- **Categories** — add, remove, or rename the folders files get sorted into
- **File paths** — log file location, credentials path

Edit `categorizer.py` to change:
- **Claude model** — swap to a different model
- **Categorization prompt** — adjust how files are classified
- **Batch size** — number of files sent per API call (default: 50)

## Project Structure

```
drive-organizer/
├── organizer.py          # Main entry point
├── drive_client.py       # Google Drive API connection and file operations
├── categorizer.py        # Claude AI file categorization
├── config.py             # Configuration (categories, paths, env vars)
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
└── com.example.drive-organizer.plist  # macOS launchd schedule template
```

## License

MIT
