//
// Created by Pavel Akhtyamov on 02.05.2020.
//

#include <fstream>
#include <sstream>

#include "WeatherTestCase.h"
#include "WeatherMock.h"
#include "cpr/cpr.h"

using ::testing::AtLeast;
using ::testing::Return;

// сформируем запрос по файлу
cpr::Response get_response(const std::int32_t status_code, std::string filename) {
  // прочитаем пример успешного запроса
  std::ifstream in_file;
  in_file.open(filename);
  std::stringstream str_stream;
  str_stream << in_file.rdbuf();
  std::string text = str_stream.str();
  in_file.close();

  cpr::Header header;
  std::string url;
  const double elapsed = 1.00;
  cpr::Cookies cookies;
  cpr::Error error;
  cpr::Response response(
    status_code, std::move(text), std::move(header), std::move(url), elapsed, 
    cookies = std::move(cookies), error = std::move(error)
  );
  return response;
}

TEST(TestGetResponseForCity, TestError) {
  WeatherMock weather;

  std::string filename = "../tests/03-weather/response_1.json";
  cpr::Response response = get_response(401, filename);

  std::string city("London");
  EXPECT_CALL(weather, Get)
    .Times(AtLeast(1))
    .WillOnce(Return(response));

  ASSERT_THROW(weather.GetResponseForCity(city), std::invalid_argument);
}

TEST(TestGetResponseForCity, TestSuccess) {
  WeatherMock weather;

  std::string filename = "../tests/03-weather/response_1.json";
  cpr::Response response = get_response(200, filename);

  std::string city("London");
  EXPECT_CALL(weather, Get)
    .Times(AtLeast(1))
    .WillOnce(Return(response));

  json our_result = weather.GetResponseForCity(city);

  std::ifstream in_file;
  in_file.open(filename);
  json true_result = json::parse(in_file);
  in_file.close();

  EXPECT_EQ(true_result, our_result);
}

TEST(TestGetTemperature, TestSuccess) {
  WeatherMock weather;

  std::string filename = "../tests/03-weather/response_1.json";
  cpr::Response response = get_response(200, filename);

  std::string city("London");
  EXPECT_CALL(weather, Get)
    .Times(AtLeast(1))
    .WillOnce(Return(response));

  float our_result = weather.GetTemperature(city);

  float true_result = 20.0;

  EXPECT_EQ(true_result, our_result);
}

TEST(TestFindDifference, TestSuccess) {
  WeatherMock weather;

  std::string filename_1 = "../tests/03-weather/response_1.json";
  cpr::Response response_1 = get_response(200, filename_1);

  std::string filename_2 = "../tests/03-weather/response_2.json";
  cpr::Response response_2 = get_response(200, filename_2);

  std::string city_1("London");
  std::string city_2("Moscow");
  EXPECT_CALL(weather, Get)
    .Times(AtLeast(2))
    .WillOnce(Return(response_1))
    .WillOnce(Return(response_2));

  json our_result = weather.FindDiffBetweenTwoCities(city_1, city_2);

  float true_result = 20.0 - 10.0;

  EXPECT_EQ(true_result, our_result);
}

TEST(TestStringDifference, NegativeDifference) {
  WeatherMock weather;

  std::string filename_1 = "../tests/03-weather/response_1.json";
  cpr::Response response_1 = get_response(200, filename_1);

  std::string filename_2 = "../tests/03-weather/response_2.json";
  cpr::Response response_2 = get_response(200, filename_2);

  std::string city_1("London");
  std::string city_2("Moscow");
  EXPECT_CALL(weather, Get)
    .Times(AtLeast(2))
    .WillOnce(Return(response_2))
    .WillOnce(Return(response_1));

  std::string our_result = weather.GetDifferenceString(city_2, city_1);
  std::string true_result = "Weather in Moscow is colder than in London by 10 degrees";

  EXPECT_STREQ(true_result.c_str(), our_result.c_str());
}

TEST(TestStringDifference, NotPositiveDifference) {
  WeatherMock weather;

  std::string filename_1 = "../tests/03-weather/response_1.json";
  cpr::Response response_1 = get_response(200, filename_1);

  std::string filename_2 = "../tests/03-weather/response_2.json";
  cpr::Response response_2 = get_response(200, filename_2);

  std::string city_1("London");
  std::string city_2("Moscow");
  EXPECT_CALL(weather, Get)
    .Times(AtLeast(2))
    .WillOnce(Return(response_1))
    .WillOnce(Return(response_2));

  std::string our_result = weather.GetDifferenceString(city_1, city_2);
  std::string true_result = "Weather in London is warmer than in Moscow by 10 degrees";

  EXPECT_STREQ(true_result.c_str(), our_result.c_str());
}