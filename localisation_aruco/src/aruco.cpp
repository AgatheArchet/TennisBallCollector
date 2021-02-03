#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/pose.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "std_msgs/msg/header.hpp"
#include <visualization_msgs/msg/marker.hpp>
#include <visualization_msgs/msg/marker_array.hpp> 

#include <opencv2/aruco.hpp>
#include <opencv2/calib3d/calib3d.hpp>
#include <geometry_msgs/msg/twist.hpp>

#include <opencv2/core/core.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <cv_bridge/cv_bridge.h>

using std::placeholders::_1;
using namespace std;
using namespace cv;
using namespace std::chrono_literals;

cv::Mat cameraMatrix, distCoeffs;
std::vector<int> markerIds;
std::vector<std::vector<cv::Point2f>> markerCorners, rejectedCandidates;
cv::Ptr<cv::aruco::Dictionary> dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_4X4_50);
float marker_length = 0.8;
cv::Mat rot_mat(3, 3, cv::DataType<float>::type);

float x_marker =-1;
float y_marker = -1; 
float yaw_marker =  -1;


// Checks if a matrix is a valid rotation matrix.
bool isRotationMatrix(Mat &R)
{
    Mat Rt;
    transpose(R, Rt);
    Mat shouldBeIdentity = Rt * R;
    Mat I = Mat::eye(3,3, shouldBeIdentity.type());
    return  norm(I, shouldBeIdentity) < 1e-6;
}

// Calculates rotation matrix to euler angles
// The result is the same as MATLAB except the order
// of the euler angles ( x and z are swapped ).
Vec3f rotationMatrixToEulerAngles(Mat &R)
{

    assert(isRotationMatrix(R));
    float sy = sqrt(R.at<double>(0,0) * R.at<double>(0,0) +  R.at<double>(1,0) * R.at<double>(1,0) );
    bool singular = sy < 1e-6; // If
    float x, y, z;
    if (!singular)
    {
        x = atan2(R.at<double>(2,1) , R.at<double>(2,2));
        y = atan2(-R.at<double>(2,0), sy);
        z = atan2(R.at<double>(1,0), R.at<double>(0,0));
    }
    else
    {
        x = atan2(-R.at<double>(1,2), R.at<double>(1,1));
        y = atan2(-R.at<double>(2,0), sy);
        z = 0;
    }
    return Vec3f(x, y, z);

}


class MinimalSubscriber : public rclcpp::Node
{
  public:
    MinimalSubscriber()
    : Node("minimal_subscriber")
    {
      subscription_ = this->create_subscription<sensor_msgs::msg::Image>(
      "/zenith_camera/image_raw", 10, std::bind(&MinimalSubscriber::image_callback, this, _1));

      publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/aruco_twist", 10);
    }

  private:
    void image_callback(const sensor_msgs::msg::Image::SharedPtr msg) const
    {
		std_msgs::msg::Header msg_header = msg->header;
		std::string frame_id = msg_header.frame_id.c_str();
		cv_bridge::CvImagePtr cv_ptr;

		try
		{
			cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::BGR8);
			Mat frame = cv_ptr->image;
			cv::Mat frameCopy;
    		frame.copyTo(frameCopy);
			
    	// detection du marker 0
		  std::vector<cv::Vec3d> rvecs, tvecs;
		  cv::aruco::detectMarkers(frameCopy, dictionary, markerCorners, markerIds);

	    visualization_msgs::msg::MarkerArray marker_array_msg;
	    marker_array_msg.markers.resize(2);

	    if (markerIds.size()>0) {
	    	// tracé des arucos sur l'image
    			cv::aruco::drawDetectedMarkers(frameCopy, markerCorners, markerIds,cv::Scalar(255, 0, 0));
    			cv::aruco::estimatePoseSingleMarkers(markerCorners, marker_length, cameraMatrix, distCoeffs, rvecs, tvecs);
    			cv::aruco::drawAxis(frameCopy, cameraMatrix, distCoeffs, rvecs, tvecs, 0.1);
    			cout << "rvec : " << rvecs[0] << endl;
    			x_marker = -tvecs[0][0];
    			y_marker = -tvecs[0][1];

    			cv::Rodrigues(rvecs[0], rot_mat);

          cv::Vec3d angles_marker = rotationMatrixToEulerAngles(rot_mat);
          yaw_marker = angles_marker[2];
          cout << yaw_marker*180/3.1415 << endl;

          auto message = geometry_msgs::msg::Twist();
          message.linear.x = -x_marker + 7.92;
          message.linear.y = y_marker + 3.18;
          message.linear.z = 0;
          message.angular.x = 0;
          message.angular.y = 0;
          message.angular.z = yaw_marker;
          publisher_->publish(message);

    			imshow("Entrée",frameCopy);
    		}else{
				  imshow("Entrée",frame);
			  }
			waitKey(3);
		}

		catch (cv_bridge::Exception& e)
		{
			RCLCPP_ERROR(this->get_logger(),"cv_bridge exception: %s", e.what());
			return;
    	}
    }

    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr subscription_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;
};


int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

    // get calibration parameters
    cv::FileStorage storage1("./localisation_aruco/src/cameraMatrix.ext", cv::FileStorage::READ);
    storage1["cameraMatrix"] >> cameraMatrix;
    storage1.release();
    cv::FileStorage storage2("./localisation_aruco/src/distCoeffs.ext", cv::FileStorage::READ);
    storage2["distCoeffs"] >> distCoeffs;
    storage2.release();

  rclcpp::spin(std::make_shared<MinimalSubscriber>());
  rclcpp::shutdown();
  return 0;
}