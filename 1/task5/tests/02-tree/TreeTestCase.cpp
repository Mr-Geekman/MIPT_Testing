//
// Created by akhtyamovpavel on 5/1/20.
//

#include <boost/filesystem.hpp>

using boost::filesystem::create_directory;
using boost::filesystem::remove_all;
using boost::filesystem::remove;
using boost::filesystem::ofstream;
using boost::filesystem::rename;


#include "TreeTestCase.h"
#include "Tree.h"

void TreeTestCaseSimple::SetUp() {
  // create directories and files
  create_directory("test_directory");
}

void TreeTestCaseSimple::TearDown() {
  // delete directories and files
  remove_all("test_directory");
}

void TreeTestCaseDifficult::SetUp() {
  // create directories and files
  create_directory("test_directory");
  ofstream("file_to_rename.txt");
  rename("file_to_rename.txt", "file.txt");

  create_directory("test_directory/inner_1");
  ofstream("test_directory/inner_1_file_to_rename.txt");
  rename("test_directory/inner_1_file_to_rename.txt", "test_directory/inner_1_file.txt");

  create_directory("test_directory/inner_1/inner_2");
}

void TreeTestCaseDifficult::TearDown() {
  // delete directories and files
  remove_all("test_directory");
  remove("file.txt");
}

TEST_F(TreeTestCaseSimple, SkipFor) {
  FileNode our_answer = GetTree("test_directory", true);
  
  std::vector<FileNode> true_answer_children;
  FileNode true_answer = {
    boost::filesystem::path("test_directory").filename().string(),
    true,
    true_answer_children
  };

  EXPECT_EQ(our_answer, true_answer);
}

TEST_F(TreeTestCaseDifficult, PathNotExists) {
  ASSERT_THROW(GetTree("invalid_path", true), std::invalid_argument);
}

TEST_F(TreeTestCaseDifficult, IsNotDirectory) {
  ASSERT_THROW(GetTree("file.txt", true), std::invalid_argument);;
}

TEST_F(TreeTestCaseDifficult, CheckDirsOnly) {
  FileNode our_answer = GetTree("test_directory", true);

  std::vector<FileNode> inner_2_children;
  FileNode inner_2 = {
    boost::filesystem::path("test_directory/inner_1/inner_2").filename().string(),
    true,
    inner_2_children
  };

  std::vector<FileNode> inner_1_children;
  inner_1_children.push_back(inner_2);
  FileNode inner_1 = {
    boost::filesystem::path("test_directory/inner_1").filename().string(),
    true,
    inner_1_children
  };

  std::vector<FileNode> test_directory_children;
  test_directory_children.push_back(inner_1);
  FileNode true_answer = {
    boost::filesystem::path("test_directory").filename().string(),
    true,
    test_directory_children
  };

  EXPECT_EQ(our_answer, true_answer);
}

TEST_F(TreeTestCaseDifficult, CheckNotDirsOnly) {
  FileNode our_answer = GetTree("test_directory", false);

  std::vector<FileNode> inner_2_children;
  FileNode inner_2 = {
    boost::filesystem::path("test_directory/inner_1/inner_2").filename().string(),
    true,
    inner_2_children
  };

  std::vector<FileNode> inner_1_children;
  inner_1_children.push_back(inner_2);
  FileNode inner_1 = {
    boost::filesystem::path("test_directory/inner_1").filename().string(),
    true,
    inner_1_children
  };
  std::vector<FileNode> true_answer_file_children;
  FileNode true_answer_file = {
    boost::filesystem::path("test_directory/inner_1_file.txt").filename().string(),
    false,
    true_answer_file_children
  };

  std::vector<FileNode> test_directory_children;
  test_directory_children.push_back(inner_1);
  test_directory_children.push_back(true_answer_file);
  FileNode true_answer = {
    boost::filesystem::path("test_directory").filename().string(),
    true,
    test_directory_children
  };

  // Порядок итерации не гарантирован, поэтому надо будет проверять children поэлементно
  EXPECT_EQ(our_answer.name, true_answer.name);
  EXPECT_EQ(our_answer.is_dir, true_answer.is_dir);
  // Проверим, что дети результата вызова -- это директория и файл
  EXPECT_EQ(our_answer.children.size(), 2);
  EXPECT_TRUE(our_answer.children[0].is_dir || our_answer.children[1].is_dir);
  EXPECT_TRUE(!our_answer.children[0].is_dir || !our_answer.children[1].is_dir);

  FileNode our_answer_inner_1 = our_answer.children[0].is_dir ? our_answer.children[0] : our_answer.children[1];
  FileNode our_answer_file = our_answer.children[1].is_dir ? our_answer.children[0] : our_answer.children[1];

  EXPECT_EQ(our_answer_file, true_answer_file);
  EXPECT_EQ(our_answer_inner_1, inner_1);
}