import React, { useState, useEffect } from 'react';
import api from '../api';
import CourseForm from '../components/CourseForm';
import CourseList from '../components/CourseList';

/**
 * Componente para a página inicial.
 * Gerencia o estado da lista de cursos e busca os dados da API.
 */
const HomePage = () => {
  const [courses, setCourses] = useState([]);

  // Busca os cursos da API quando o componente é montado
  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await api.get('/courses');
        setCourses(response.data);
      } catch (error) {
        console.error('Erro ao buscar cursos:', error);
      }
    };
    fetchCourses();
  }, []);

  // Callback para atualizar a lista de cursos quando um novo curso é adicionado
  const handleCourseAdded = (newCourse) => {
    setCourses([...courses, newCourse]);
  };

  return (
    <>
      <CourseForm onCourseAdded={handleCourseAdded} />
      <CourseList courses={courses} />
    </>
  );
};

export default HomePage;
