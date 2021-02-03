#include <opencv2/aruco.hpp>
#include <opencv2/opencv.hpp>



cv::Mat cameraMatrix, distCoeffs;
// camera parameters are read from somewhere
cv::Ptr<cv::aruco::Dictionary> dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_6X6_250);

cv::Mat image = cv::imread("test.png");
// std::vector<int> ids;
// std::vector<std::vector<cv::Point2f>> corners;
// cv::aruco::detectMarkers(frame, dictionary, markerCorners, markerIds);
// // if at least one marker detected
// if (ids.size() > 0) {
//     cv::aruco::drawDetectedMarkers(image, corners, ids);
//     std::vector<cv::Vec3d> rvecs, tvecs;
    
cv::imshow("out", image);


