from utils import read_video, save_video
from trackers import Tracker
import cv2
import numpy as np
import os
import sys

from team_assigner import TeamAssigner
from player_ball_assigner import PlayerBallAssigner
from camera_movement_estimator import CameraMovementEstimator
from view_transformer import ViewTransformer
from speed_and_distance_estimator import SpeedAndDistance_Estimator

# Define BASE_DIR to avoid incorrect paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Correct file paths
MODEL_PATH = os.path.join(BASE_DIR, "models", "best.pt")
STUB_PATH = os.path.join(BASE_DIR, "stubs", "track_stubs.pkl")

def process_video(input_path, output_path):
    print(f"Processing video: {input_path}")

    if not os.path.exists(input_path):
        print(f"Error: File {input_path} not found!")
        return None

    video_frames = read_video(input_path)
    if len(video_frames) == 0:
        print("Error: No frames extracted. Video might be corrupted.")
        return None

    # Initialize Tracker
    tracker = Tracker(MODEL_PATH)

    tracks = tracker.get_object_tracks(video_frames,
                                       read_from_stub=False,
                                       stub_path=STUB_PATH)

    # Get object positions 
    tracker.add_position_to_tracks(tracks)

    # Camera movement estimator
    camera_movement_estimator = CameraMovementEstimator(video_frames[0])
    camera_movement_per_frame = camera_movement_estimator.get_camera_movement(
        video_frames, read_from_stub=True, stub_path=os.path.join(BASE_DIR, "stubs", "camera_movement_stub.pkl"))

    camera_movement_estimator.add_adjust_positions_to_tracks(tracks, camera_movement_per_frame)

    # View Transformer
    view_transformer = ViewTransformer(recompute_matrix=True)
    view_transformer.add_transformed_position_to_tracks(tracks)

    # Interpolate Ball Positions
    tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])

    # Speed and distance estimator
    speed_and_distance_estimator = SpeedAndDistance_Estimator()
    speed_and_distance_estimator.add_speed_and_distance_to_tracks(tracks)

    # Assign Player Teams
    team_assigner = TeamAssigner()
    team_assigner.assign_team_color(video_frames[0], tracks['players'][0])

    # Assign Ball Acquisition
    player_assigner = PlayerBallAssigner()
    team_ball_control = []

    for frame_num in range(min(len(video_frames), len(tracks["players"]))):
        player_track = tracks["players"][frame_num]

        if frame_num not in tracks['ball'] or 1 not in tracks['ball'][frame_num]:
            team_ball_control.append(team_ball_control[-1] if team_ball_control else -1)
            continue

        ball_bbox = tracks['ball'][frame_num][1]['bbox']
        assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox, frame_num)

        if assigned_player != -1:
            tracks['players'][frame_num][assigned_player]['has_ball'] = True

            if 'team' not in tracks['players'][frame_num][assigned_player]:
                team = team_assigner.get_player_team(video_frames[frame_num],
                                                     tracks['players'][frame_num][assigned_player]['bbox'],
                                                     assigned_player)
                tracks['players'][frame_num][assigned_player]['team'] = team
                tracks['players'][frame_num][assigned_player]['team_color'] = team_assigner.team_colors[team]

            team_ball_control.append(tracks['players'][frame_num][assigned_player]['team'])
        else:
            team_ball_control.append(team_ball_control[-1] if team_ball_control else -1)

    # Draw output
    team_ball_control = np.array(team_ball_control)
    output_video_frames = tracker.draw_annotations(video_frames, tracks, team_ball_control)

    # Draw Camera movement
    output_video_frames = camera_movement_estimator.draw_camera_movement(output_video_frames, camera_movement_per_frame)

    # Draw Speed and Distance
    speed_and_distance_estimator.draw_speed_and_distance(output_video_frames, tracks)

    # Save video
    save_video(output_video_frames, output_path)

    if os.path.exists(output_path):
        print(f"Processed video saved at: {output_path}")
    else:
        print(f"Error: Processed video was not saved at {output_path}")

    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_video_path> <output_video_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    # Ensure paths are absolute before processing
    input_path = os.path.join(BASE_DIR, "uploads", os.path.basename(input_path))
    output_path = os.path.join(BASE_DIR, "static", os.path.basename(output_path))

    process_video(input_path, output_path)

